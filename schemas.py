from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


class FactAdMetricsDailySchemas(BaseModel):
    advertise_id: str
    likes: Optional[bool] = False
    impressions: Optional[bool] = False
    clicks: Optional[str] = None
    conversions: Optional[bool] = False
    register_user: Optional[str] = None
    guest_user: Optional[str] = None
    dim_date_id: Optional[str] = None
    platform_id: Optional[str] = None
    gender_id: Optional[str] = None
    device_type_id: Optional[str] = None
    region_id: Optional[str] = None

    class Config:
        from_attributes = True


class AdvertisementSchema(BaseModel):
    id: Optional[str] = None
    ad_promot_company_name: Optional[str] = None
    ad_message: Optional[str] = None
    buy_url: Optional[str] = None
    ad_run_hours: Optional[str] = None
    ad_cost: Optional[str] = None
    is_ad_active: Optional[bool] = None
    advertise_end_date: Optional[str] = None
    advertise_end_time: Optional[str] = None
    user: Optional[str] = None

    class Config:
        from_attributes = True


class UserSchemas(BaseModel):
    id: Optional[str] = None
    Name: str
    email: EmailStr
    dateofbirth: str
    gender: str
    is_superadmin: Optional[bool] = None
    age_range: Optional[str] = None
    gender: Optional[str] = None
    password: Optional[str] = None

    @validator("dateofbirth", pre=True, always=True)
    def validate_date_format(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

    @validator("gender", pre=True, always=True)
    def validate_gender(cls, v):
        if v is None:
            return v
        valid_genders = ["male", "female", "other", "unknown"]
        if v.lower() not in valid_genders:
            raise ValueError(f"Gender must be one of {valid_genders}")
        return v.lower()

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str


class UserLogin(BaseModel):
    email: str
    password: str
