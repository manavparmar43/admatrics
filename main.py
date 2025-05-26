from fastapi import FastAPI, status, Request, Depends, Header, Query
from fastapi.responses import JSONResponse, HTMLResponse
from database_connection import Base, engine
from fastapi.security import OAuth2PasswordRequestForm
import json, os

from fastapi.middleware.cors import CORSMiddleware
from config import MIDDLEWARE_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from starlette.middleware.sessions import SessionMiddleware
from fastapi import BackgroundTasks, Form
from database_connection import Base, get_db
from models import *
from sqlalchemy.orm import Session
from schemas import (
    UserLogin,
    UserSchemas,
    Token,
    FactAdMetricsDailySchemas,
    AdvertisementSchema,
)
import uvicorn
from scheduler import setup_scheduler, scheduler
from typing import Optional, List
from controllers import (
    create_user_data,
    fact_ad_daily_report_manage,
    create_adverise_controller,
    create_fact_ad_daily_report,
)
from datetime import timedelta
from authentication import (
    create_access_token,
    authenticate_user,
    oauth2_scheme,
    decode_access_token,
)
from fastapi import HTTPException, status

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["content-type", "authorization", "advertisement_id", "token"],
)

app.add_middleware(SessionMiddleware, secret_key=MIDDLEWARE_KEY)


@app.post("/users/", response_model=UserSchemas)
def create_user(user_data: UserSchemas, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email Already Used...!",
        )
    created_user_data = create_user_data(db, user_data)
    return created_user_data


@app.post("/create-advertise/", response_model=AdvertisementSchema)
async def create_advertise(
    ad_data: AdvertisementSchema,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    response_data = create_adverise_controller(db=db, ad_data=ad_data, token=token)
    return response_data


@app.post("/create/fact-ad-matrics/", response_model=FactAdMetricsDailySchemas)
async def fact_ad_matrics_manage(
    admatrics_data: FactAdMetricsDailySchemas,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    response_data = fact_ad_daily_report_manage(
        db=db, admatrics_data=admatrics_data, token=token
    )
    return response_data


# This is a example of buy URL  accessible only to registered users. Each visit counts as a conversion and increments the click count by one
@app.get("/")
async def buy_conversions(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    advertisement_id: Optional[str] = Header(..., alias="advertisement_id"),
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please Login First...!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(token=token).get("id")
    fact_ad_matrics_obj = (
        db.query(FactAdMetricsDaily)
        .filter(
            FactAdMetricsDaily.register_user == user_id,
            FactAdMetricsDaily.advertise_id == advertisement_id,
        )
        .first()
    )
    if not fact_ad_matrics_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ad metrics not found"
        )

    dates = (
        db.query(DimDates)
        .filter(DimDates.id == fact_ad_matrics_obj.dim_date_id)
        .first()
    )
    if not dates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Date not found"
        )

    if dates.date_created != datetime.now().strftime("%Y-%m-%d"):
        fact_ad_matrics_new_obj = create_fact_ad_daily_report(
            advertise_id=advertisement_id,
            user_id=user_id,
            db=db,
            likes=fact_ad_matrics_obj.likes,
        )
        fact_ad_matrics_new_obj.conversions = True
        fact_ad_matrics_new_obj.clicks = int(fact_ad_matrics_new_obj.clicks) + 1
        db.commit()
        response_data = FactAdMetricsDailySchemas.model_validate(
            fact_ad_matrics_new_obj
        )
    elif not fact_ad_matrics_obj.conversions:
        fact_ad_matrics_obj.conversions = True
        fact_ad_matrics_obj.clicks = int(fact_ad_matrics_obj.clicks) + 1
        db.commit()
        response_data = FactAdMetricsDailySchemas.model_validate(fact_ad_matrics_obj)
    else:
        fact_ad_matrics_obj.clicks = int(fact_ad_matrics_obj.clicks) + 1
        db.commit()
        response_data = FactAdMetricsDailySchemas.model_validate(fact_ad_matrics_obj)

    return JSONResponse(
        status_code=status.HTTP_200_OK, content={"data": response_data.model_dump()}
    )


@app.post("/login-user/", response_model=Token)
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"id": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token}


@app.get("/cron-status")
async def get_cron_status():
    try:
        job = scheduler.get_job("log_timestamp_job")
        if job:
            return {
                "status": "running",
                "next_run": str(job.next_run_time),
                "job_id": job.id,
            }
        return {"status": "not_found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/fact-ad-metrics/", response_model=List[FactAdMetricsDailySchemas])
async def get_fact_ad_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    platform_id: Optional[str] = Query(None),
    device_type_id: Optional[str] = Query(None),
    gender_id: Optional[str] = Query(None),
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please Login First...!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be in YYYY-MM-DD format",
            )
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date must be in YYYY-MM-DD format",
            )

    query = db.query(FactAdMetricsDaily)

    if start_date or end_date:
        query = query.join(DimDates, FactAdMetricsDaily.dim_date_id == DimDates.id)
        if start_date:
            query = query.filter(DimDates.date_created >= start_date)
        if end_date:
            query = query.filter(DimDates.date_created <= end_date)

    elif region_id:
        query = query.filter(FactAdMetricsDaily.region_id == region_id)
    elif platform_id:
        query = query.filter(FactAdMetricsDaily.platform_id == platform_id)
    elif device_type_id:
        query = query.filter(FactAdMetricsDaily.device_type_id == device_type_id)
    elif gender_id:
        query = query.filter(FactAdMetricsDaily.gender_id == gender_id)

    results = query.all()
    if not results:
        return []

    response_data = [
        FactAdMetricsDailySchemas.model_validate(result) for result in results
    ]
    return response_data


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()


@app.on_event("startup")
async def on_event():
    setup_scheduler()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
