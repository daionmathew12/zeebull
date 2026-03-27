from pydantic import BaseModel
from datetime import date

# Base schema with is_active
class BaseSchema(BaseModel):
    is_active: bool = True
    branch_id: int | None = None
    branch_name: str | None = None

    class Config:
        from_attributes = True


# Header & Banner
class HeaderBannerBase(BaseSchema):
    title: str
    subtitle: str
    image_url: str
    branch_id: int | None = None

class HeaderBannerCreate(HeaderBannerBase):
    pass

class HeaderBannerUpdate(BaseSchema):
    title: str | None = None
    subtitle: str | None = None
    image_url: str | None = None
    branch_id: int | None = None

class HeaderBanner(HeaderBannerBase):
    id: int


# Check Availability
class CheckAvailabilityBase(BaseSchema):
    name: str
    email: str
    phone: str
    check_in: date
    check_out: date
    guests: int

class CheckAvailabilityCreate(CheckAvailabilityBase):
    pass

class CheckAvailability(CheckAvailabilityBase):
    id: int


# Gallery
class GalleryBase(BaseSchema):
    image_url: str
    caption: str

class GalleryCreate(GalleryBase):
    pass

class Gallery(GalleryBase):
    id: int


# Reviews
class ReviewBase(BaseSchema):
    name: str
    comment: str
    rating: int

class ReviewCreate(ReviewBase):
    pass

class Review(ReviewBase):
    id: int


# Resort Info
class ResortInfoBase(BaseSchema):
    name: str
    address: str
    facebook: str | None = None
    instagram: str | None = None
    twitter: str | None = None
    linkedin: str | None = None

class ResortInfoCreate(ResortInfoBase):
    pass

class ResortInfo(ResortInfoBase):
    id: int


# Signature Experiences
class SignatureExperienceBase(BaseSchema):
    title: str
    description: str
    image_url: str
    extra_images: str | None = None

class SignatureExperienceCreate(SignatureExperienceBase):
    pass

class SignatureExperienceUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    branch_id: int | None = None

class SignatureExperience(SignatureExperienceBase):
    id: int


# Plan Your Wedding
class PlanWeddingBase(BaseSchema):
    title: str
    description: str
    image_url: str
    extra_images: str | None = None

class PlanWeddingCreate(PlanWeddingBase):
    pass

class PlanWeddingUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    branch_id: int | None = None

class PlanWedding(PlanWeddingBase):
    id: int


# Nearby Attractions
class NearbyAttractionBase(BaseSchema):
    title: str
    description: str
    image_url: str
    extra_images: str | None = None
    map_link: str | None = None


class NearbyAttractionCreate(NearbyAttractionBase):
    pass


class NearbyAttractionUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    map_link: str | None = None
    branch_id: int | None = None


class NearbyAttraction(NearbyAttractionBase):
    id: int


# Nearby Attraction Banners
class NearbyAttractionBannerBase(BaseSchema):
    title: str
    subtitle: str
    image_url: str
    extra_images: str | None = None
    map_link: str | None = None


class NearbyAttractionBannerCreate(NearbyAttractionBannerBase):
    pass


class NearbyAttractionBannerUpdate(BaseSchema):
    title: str | None = None
    subtitle: str | None = None
    image_url: str | None = None
    map_link: str | None = None
    branch_id: int | None = None


class NearbyAttractionBanner(NearbyAttractionBannerBase):
    id: int