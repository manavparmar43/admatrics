from sqlalchemy.orm import Session
from typing import Optional
from schemas import UserSchemas, FactAdMetricsDailySchemas, AdvertisementSchema
from models import (
    DimDates,
    DimAgeGroup,
    DimRegion,
    DimPlatform,
    DimDeviceType,
    DimGender,
    User,
    FactAdMetricsDaily,
    Guestuser,
    Advertisement,
)
from fastapi import HTTPException
from datetime import datetime, timedelta
from generate_system_report import get_current_info
import bcrypt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from authentication import decode_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hash_password(password: str):
    return pwd_context.hash(password)


def calculate_advertise_end_datetime(hours):
    now = datetime.now()
    future_time = now + timedelta(hours=hours)

    ad_endtime = future_time.strftime("%H:%M")

    ad_enddate = future_time.strftime("%Y-%m-%d")

    return ad_enddate, ad_endtime


def calculate_age(birth_date_str):
    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
    today = datetime.today()

    age = today.year - birth_date.year

    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age


def get_or_create_gender(db: Session, gender: str = None) -> DimGender:
    gender = gender or "unknown"
    gender_data = db.query(DimGender).filter(DimGender.gender == gender).first()
    if gender_data:
        return gender_data
    new_record = DimGender(gender=gender.lower())
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record


def get_dim_dates(db: Session):
    record = DimDates(
        date_created=datetime.now().strftime("%Y-%m-%d"),
        time_created=datetime.now().strftime("%H:%M"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_dim_region(db: Session):
    current_info = get_current_info()
    record = DimRegion(
        regionname=current_info["region"],
        cityname=current_info["city"],
        countryname=current_info["country"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_dim_device_info(db: Session):
    current_info = get_current_info()
    record = DimDeviceType(
        device_name=f"{current_info['device_company']} {current_info['device_type']}"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_dim_platform_info(db: Session):
    current_info = get_current_info()
    record = DimPlatform(
        platform_name=current_info["platform"],
        platform_hostname=current_info["platform_hostname"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_guest_user(db: Session):
    current_info = get_current_info()
    record = Guestuser(
        ip_address=current_info["ip"],
        guest_name=current_info["name"],
        location=current_info["location"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record.id


def get_age(db: Session, dob):
    age = calculate_age(dob)
    record = DimAgeGroup(age_range=age)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def create_user_data(db: Session, user_data: UserSchemas):
    try:
        hashed_password = hash_password(user_data.password)
        age_group_id = get_age(db, user_data.dateofbirth)
        gender_id = get_or_create_gender(db=db, gender=user_data.gender)
        user = User(
            Name=user_data.Name,
            email=user_data.email,
            dateofbirth=user_data.dateofbirth,
            is_superadmin=user_data.is_superadmin,
            agegroup_id=age_group_id.id,
            gender_id=gender_id.id,
            password=hashed_password,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        response_data = UserSchemas(
            id=user.id,
            Name=user.Name,
            email=user.email,
            dateofbirth=user.dateofbirth,
            is_superadmin=user.is_superadmin,
            age_range=age_group_id.age_range,
            gender=gender_id.gender,
            password=user.password,
        )

        return response_data
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error saving data: {str(e)}")
    finally:
        db.close()


def create_adverise(db: Session, ad_data: AdvertisementSchema, token=None):
    try:

        user_id = decode_access_token(token=token).get("id")
        if not db.query(User).filter(User.id == user_id).first():
            raise HTTPException(status_code=400, detail=f"Token not Valid...!")
        add_cost_cal = 100 * int(ad_data.ad_run_hours)
        ad_enddate, ad_endtime = calculate_advertise_end_datetime(
            int(ad_data.ad_run_hours)
        )
        new_ad = Advertisement(
            ad_promot_company_name=ad_data.ad_promot_company_name,
            ad_message=ad_data.ad_message,
            ad_run_hours=ad_data.ad_run_hours,
            ad_cost=add_cost_cal,
            is_ad_active=True,
            advertise_end_date=ad_enddate,
            advertise_end_time=ad_endtime,
            user=user_id,
        )

        db.add(new_ad)
        db.commit()
        db.refresh(new_ad)

        return new_ad

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error saving advertisement: {str(e)}"
        )
    finally:
        db.close()


def create_fact_ad_daily_report(
    db: Session, user_id=None, likes=None, advertise_id=None
):
    try:
        region_id = get_dim_region(db)
        date_id = get_dim_dates(db)
        device_id = get_dim_device_info(db)
        platform_id = get_dim_platform_info(db)
        ad_metrics_data = {
            "advertise_id": advertise_id,
            "impressions": True,
            "dim_date_id": date_id.id,
            "platform_id": platform_id.id,
            "device_type_id": device_id.id,
            "region_id": region_id.id,
            "likes": True if likes else False,
            "register_user": user_id if user_id else None,
            "guest_user": get_guest_user(db) if user_id == None else None,
            "gender_id": (
                get_or_create_gender(db=db).id
                if user_id == None
                else db.query(User).filter(User.id == user_id).first().gender_id
            ),
        }
        ad_matrics = FactAdMetricsDaily(**ad_metrics_data)
        db.add(ad_matrics)
        db.commit()
        db.refresh(ad_matrics)

        return ad_matrics

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error saving data: {str(e)}")
    finally:
        db.close()


def fact_ad_daily_report_manage(
    db: Session, admatrics_data: FactAdMetricsDailySchemas, token=None
):
    try:
        if token:
            user_id = decode_access_token(token).get("id")
            fact_ad_register_user = (
                db.query(FactAdMetricsDaily)
                .filter(
                    FactAdMetricsDaily.register_user == user_id,
                    FactAdMetricsDaily.advertise_id == admatrics_data.advertise_id,
                )
                .first()
            )
            if fact_ad_register_user:
                fact_ad_register_user.likes = admatrics_data.likes
                db.commit()
                update_response_data = FactAdMetricsDailySchemas.model_validate(
                    fact_ad_register_user
                )
                return update_response_data

            elif admatrics_data.likes or admatrics_data.likes == False:
                data = create_fact_ad_daily_report(
                    user_id=user_id,
                    advertise_id=admatrics_data.advertise_id,
                    likes=admatrics_data.likes,
                    db=db,
                )
                response_data = FactAdMetricsDailySchemas.model_validate(data)

        else:
            if admatrics_data.likes:
                raise HTTPException(status_code=400, detail="Please Login First...!")
            data = create_fact_ad_daily_report(
                advertise_id=admatrics_data.advertise_id, db=db
            )
            response_data = FactAdMetricsDailySchemas.model_validate(data)
        return response_data

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error saving data: {str(e)}")
    finally:
        db.close()
