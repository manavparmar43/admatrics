from sqlalchemy import Column, String, Text, ForeignKey, Boolean
from database_connection import Base
from datetime import datetime
import uuid


class DimDates(Base):
    __tablename__ = "dimdates"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    date_created = Column(String, index=True)
    time_created = Column(String, index=True)


class DimRegion(Base):
    __tablename__ = "dimregion"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    regionname = Column(String, index=True)
    cityname = Column(String, index=True)
    countryname = Column(String, index=True)


class DimAgeGroup(Base):
    __tablename__ = "dimagegroup"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    age_range = Column(String, index=True)


class DimGender(Base):
    __tablename__ = "dimgender"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    gender = Column(String, index=True)


class DimPlatform(Base):
    __tablename__ = "dimplatform"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    platform_name = Column(String, index=True)
    platform_hostname = Column(String, index=True)


class DimDeviceType(Base):
    __tablename__ = "dimdevicetype"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    device_name = Column(String, index=True)


class User(Base):
    __tablename__ = "user"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    Name = Column(String, index=True)
    email = Column(String, index=True)
    password = Column(String, index=True)
    dateofbirth = Column(String, index=True)
    is_superadmin = Column(Boolean, default=False)
    gender_id = Column(String, ForeignKey("dimgender.id"), index=True)
    agegroup_id = Column(String, ForeignKey("dimagegroup.id"), index=True)
    created_date = Column(String, default=lambda: datetime.now().strftime("%d-%m-%Y"))
    created_time = Column(String, default=lambda: datetime.now().strftime("%H:%M:%S"))


class Guestuser(Base):
    __tablename__ = "guest_user"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    ip_address = Column(String, index=True)
    guest_name = Column(String, index=True)
    location = Column(String, index=True)


class Advertisement(Base):
    __tablename__ = "advertisement"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    ad_promot_company_name = Column(String, index=True)
    ad_message = Column(Text, nullable=True)
    buy_url = Column(Text, nullable=True, default="http://localhost:8000")
    ad_run_hours = Column(String, index=True)
    ad_cost = Column(String, index=True, default="0")
    is_ad_active = Column(Boolean, default=True)
    advertise_end_date = Column(String, index=True)
    advertise_end_time = Column(String, index=True)
    user = Column(String, ForeignKey("user.id"), index=True, nullable=True)


class FactAdMetricsDaily(Base):

    __tablename__ = "fact_admetrics_daily"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        index=True,
    )
    advertise_id = Column(
        String, ForeignKey("advertisement.id"), index=True, nullable=True
    )
    impressions = Column(Boolean, index=True, default=False)
    clicks = Column(String, index=True, default="0")
    likes = Column(Boolean, index=True, default=False)
    conversions = Column(Boolean, index=True, default=False)
    register_user = Column(String, ForeignKey("user.id"), index=True, nullable=True)
    guest_user = Column(String, ForeignKey("guest_user.id"), index=True, nullable=True)
    dim_date_id = Column(String, ForeignKey("dimdates.id"), index=True, nullable=True)
    platform_id = Column(
        String, ForeignKey("dimplatform.id"), index=True, nullable=True
    )
    device_type_id = Column(
        String, ForeignKey("dimdevicetype.id"), index=True, nullable=True
    )
    region_id = Column(String, ForeignKey("dimregion.id"), index=True, nullable=True)
    gender_id = Column(String, ForeignKey("dimgender.id"), index=True)
