from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import (
    get_current_user,
    get_optional_current_user,
)


from app.models.marketplace_product import MarketplaceProduct
from app.models.product_post import ProductPost
from app.models.product_post_publication import ProductPostPublication

from app.services.image_service import ImageService
from app.services.facebook_service import FacebookService
from app.services.instagram_service import InstagramService
from app.services.tiktok_service import TikTokService


router = APIRouter(
    prefix="/product-post",
    tags=["Product Post"],
)


# ============================================================
# REQUEST MODELS
# ============================================================


class ProductPostCreateRequest(BaseModel):
    product_id: int
    affiliate_url: str | None = None


class ProductPostPublishRequest(BaseModel):
    platforms: list[str]


# ============================================================
# CREATE PRODUCT POST
# ============================================================


@router.post("/create")
async def create_product_post(
    request: ProductPostCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):

    # --------------------------------------------------------
    # Find product
    # --------------------------------------------------------

    product = (
        db.query(MarketplaceProduct)
        .filter(
            MarketplaceProduct.id == request.product_id,
            MarketplaceProduct.status == "active",
        )
        .first()
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    # --------------------------------------------------------
    # Affiliate URL
    # --------------------------------------------------------
    #
    # If the influencer supplied a generated affiliate URL,
    # use it for promotion.
    #
    # Otherwise preserve the original product URL.
    # --------------------------------------------------------

    promotion_url = (
        request.affiliate_url
        if request.affiliate_url
        else product.product_url
    )

    # --------------------------------------------------------
    # Generate promotional image
    # --------------------------------------------------------

    image_service = ImageService()

    try:

        image = await image_service.create_product_image(
            product
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to generate product image: "
                f"{str(e)}"
            ),
        )

    # --------------------------------------------------------
    # Social media title
    # --------------------------------------------------------

    title = product.title

    # --------------------------------------------------------
    # Social media caption
    # --------------------------------------------------------

    caption_parts = []

    caption_parts.append(
        f"🔥 {product.title}"
    )

    caption_parts.append("")

    if product.description:

        caption_parts.append(
            product.description
        )

        caption_parts.append("")

    caption_parts.append(
        f"💰 Price: ₹{float(product.price):,.2f}"
    )

    # Commission intentionally not included
    #
    # caption_parts.append(
    #     f"💸 Commission: "
    #     f"{float(product.commission_percentage):.2f}%"
    # )

    caption_parts.append("")

    caption_parts.append(
        "🛒 Check it out here:"
    )

    caption_parts.append(
        promotion_url
    )

    caption_parts.append("")

    caption_parts.append(
        "#Rmworkz #Deals #Shopping #OnlineShopping"
    )

    if product.category:

        caption_parts.append(
            f"#{product.category.replace(' ', '')}"
        )

    caption = "\n".join(
        caption_parts
    )

    # --------------------------------------------------------
    # Save Product Post
    # --------------------------------------------------------

    post = ProductPost(
        product_id=product.id,
        title=title,
        caption=caption,
        image_url=image["url"],
        tiktok_jpg_url=image.get("tiktok_jpg_url"),
        product_url=promotion_url,
        status="draft",
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "success": True,

        "post": {
            "id": post.id,
            "product_id": post.product_id,
            "title": post.title,
            "caption": post.caption,
            "image_url": post.image_url,
            "tiktok_jpg_url": post.tiktok_jpg_url,
            "product_url": post.product_url,
            "status": post.status,
            "created_at": post.created_at,
        },

        "product": {
            "id": product.id,
            "brand_id": product.brand_id,
            "title": product.title,
            "description": product.description,
            "price": float(product.price),
            "commission_percentage": float(
                product.commission_percentage
            ),
            "product_url": product.product_url,
            "image_url": product.image_url,
            "category": product.category,
        },

        "image": image,
    }


# ============================================================
# GET PRODUCT POST
# ============================================================


@router.get("/{post_id}")
async def get_product_post(
    post_id: int,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Find product post
    # --------------------------------------------------------

    post = (
        db.query(ProductPost)
        .filter(
            ProductPost.id == post_id
        )
        .first()
    )

    if not post:

        raise HTTPException(
            status_code=404,
            detail="Product post not found.",
        )

    # --------------------------------------------------------
    # Find associated product
    # --------------------------------------------------------

    product = (
        db.query(MarketplaceProduct)
        .filter(
            MarketplaceProduct.id == post.product_id
        )
        .first()
    )

    # --------------------------------------------------------
    # Get publication records
    # --------------------------------------------------------

    publications = (
        db.query(ProductPostPublication)
        .filter(
            ProductPostPublication.product_post_id == post.id
        )
        .order_by(
            ProductPostPublication.id
        )
        .all()
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "success": True,

        "post": {
            "id": post.id,
            "product_id": post.product_id,
            "title": post.title,
            "caption": post.caption,
            "image_url": post.image_url,
            "tiktok_jpg_url": post.tiktok_jpg_url,
            "product_url": post.product_url,
            "status": post.status,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
        },

        "product": (
            {
                "id": product.id,
                "brand_id": product.brand_id,
                "title": product.title,
                "description": product.description,
                "price": float(product.price),
                "commission_percentage": float(
                    product.commission_percentage
                ),
                "product_url": product.product_url,
                "image_url": product.image_url,
                "category": product.category,
            }
            if product
            else None
        ),

        "publications": [
            {
                "id": publication.id,
                "platform": publication.platform,
                "status": publication.status,
                "platform_post_id": (
                    publication.platform_post_id
                ),
                "platform_post_url": (
                    publication.platform_post_url
                ),
                "error_message": (
                    publication.error_message
                ),
                "published_at": (
                    publication.published_at
                ),
                "created_at": publication.created_at,
                "updated_at": publication.updated_at,
            }
            for publication in publications
        ],
    }


# ============================================================
# PUBLISH PRODUCT POST
# ============================================================


@router.post("/{post_id}/publish")
async def publish_product_post(
    post_id: int,
    request: ProductPostPublishRequest,
    db: Session = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
):

    # --------------------------------------------------------
    # Validate platforms
    # --------------------------------------------------------

    allowed_platforms = {
        "facebook",
        "instagram",
        "instagram_story",
        "tiktok",
    }

    if not request.platforms:

        raise HTTPException(
            status_code=400,
            detail="At least one platform must be selected.",
        )

    # --------------------------------------------------------
    # Normalize platform names
    # --------------------------------------------------------

    platforms = [
        platform.strip().lower()
        for platform in request.platforms
        if platform and platform.strip()
    ]

    # --------------------------------------------------------
    # Remove duplicates while preserving order
    # --------------------------------------------------------

    platforms = list(
        dict.fromkeys(platforms)
    )

    # --------------------------------------------------------
    # Validate platforms
    # --------------------------------------------------------

    invalid_platforms = [
        platform
        for platform in platforms
        if platform not in allowed_platforms
    ]

    if invalid_platforms:

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid platform.",
                "invalid_platforms": invalid_platforms,
                "allowed_platforms": sorted(
                    allowed_platforms
                ),
            },
        )

    # --------------------------------------------------------
    # Find Product Post
    # --------------------------------------------------------

    post = (
        db.query(ProductPost)
        .filter(
            ProductPost.id == post_id
        )
        .first()
    )

    if not post:

        raise HTTPException(
            status_code=404,
            detail="Product post not found.",
        )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Only publish to platforms explicitly selected
    # by the frontend.
    #
    # We do NOT automatically publish to all platforms.
    # --------------------------------------------------------

    results = []

    successful_count = 0
    failed_count = 0

    facebook_service = None
    instagram_service = None

    # ========================================================
    # PROCESS EACH SELECTED PLATFORM
    # ========================================================

    for platform in platforms:

        # ----------------------------------------------------
        # Check if this platform was already published
        # ----------------------------------------------------

        existing_publication = (
            db.query(ProductPostPublication)
            .filter(
                ProductPostPublication.product_post_id
                == post.id,

                ProductPostPublication.platform
                == platform,

                ProductPostPublication.status
                == "published",
            )
            .first()
        )

        if existing_publication:

            results.append(
                {
                    "platform": platform,
                    "success": True,
                    "status": "already_published",
                    "platform_post_id": (
                        existing_publication.platform_post_id
                    ),
                    "platform_post_url": (
                        existing_publication.platform_post_url
                    ),
                }
            )

            successful_count += 1

            continue

        # ----------------------------------------------------
        # Create publication record
        # ----------------------------------------------------

        publication = ProductPostPublication(
            product_post_id=post.id,
            platform=platform,
            status="pending",
        )

        db.add(publication)
        db.commit()
        db.refresh(publication)

        # ====================================================
        # FACEBOOK
        # ====================================================

        if platform == "facebook":

            try:

                if facebook_service is None:

                    facebook_service = FacebookService()

                result = (
                    await facebook_service.publish_image_post(
                        image_url=post.image_url,
                        caption=post.caption,
                    )
                )

                platform_post_id = (
                    result.get("id")
                    if isinstance(result, dict)
                    else None
                )

                platform_post_url = None

                if platform_post_id:

                    platform_post_url = (
                        "https://www.facebook.com/"
                        f"{platform_post_id}"
                    )

                publication.status = "published"

                publication.platform_post_id = (
                    platform_post_id
                )

                publication.platform_post_url = (
                    platform_post_url
                )

                publication.published_at = (
                    datetime.utcnow()
                )

                publication.error_message = None

                db.commit()
                db.refresh(publication)

                successful_count += 1

                results.append(
                    {
                        "platform": "facebook",
                        "success": True,
                        "status": "published",
                        "publication_id": (
                            publication.id
                        ),
                        "platform_post_id": (
                            platform_post_id
                        ),
                        "platform_post_url": (
                            platform_post_url
                        ),
                    }
                )

            except Exception as e:

                db.rollback()

                publication = (
                    db.query(
                        ProductPostPublication
                    )
                    .filter(
                        ProductPostPublication.id
                        == publication.id
                    )
                    .first()
                )

                publication.status = "failed"

                publication.error_message = str(e)

                db.commit()

                failed_count += 1

                results.append(
                    {
                        "platform": "facebook",
                        "success": False,
                        "status": "failed",
                        "publication_id": (
                            publication.id
                        ),
                        "error_message": str(e),
                    }
                )

        # ====================================================
        # INSTAGRAM
        # ====================================================

        elif platform == "instagram":

            try:

                if instagram_service is None:

                    instagram_service = InstagramService()

                # ------------------------------------------------
                # Step 1: Create Instagram Media Container
                # ------------------------------------------------

                media = (
                    await instagram_service.create_media_container(
                        image_url=post.image_url,
                        caption=post.caption,
                    )
                )

                creation_id = media.get("id")

                if not creation_id:

                    raise Exception(
                        "Instagram did not return "
                        "a creation ID."
                    )

                # ------------------------------------------------
                # Step 2: Wait for media processing
                # ------------------------------------------------

                await instagram_service.wait_until_ready(
                    creation_id
                )

                # ------------------------------------------------
                # Step 3: Publish Media
                # ------------------------------------------------

                publish_result = (
                    await instagram_service.publish_media(
                        creation_id
                    )
                )

                media_id = publish_result.get("id")

                if not media_id:

                    raise Exception(
                        "Instagram did not return "
                        "a media ID."
                    )

                # ------------------------------------------------
                # Step 4: Get permalink
                # ------------------------------------------------

                media_details = (
                    await instagram_service.meta
                    .get_instagram_media(
                        media_id
                    )
                )

                platform_post_url = (
                    media_details.get("permalink")
                )

                # ------------------------------------------------
                # Update publication
                # ------------------------------------------------

                publication.status = "published"

                publication.platform_post_id = (
                    media_id
                )

                publication.platform_post_url = (
                    platform_post_url
                )

                publication.published_at = (
                    datetime.utcnow()
                )

                publication.error_message = None

                db.commit()
                db.refresh(publication)

                successful_count += 1

                results.append(
                    {
                        "platform": "instagram",
                        "success": True,
                        "status": "published",
                        "publication_id": (
                            publication.id
                        ),
                        "platform_post_id": (
                            media_id
                        ),
                        "platform_post_url": (
                            platform_post_url
                        ),
                    }
                )

            except Exception as e:

                db.rollback()

                publication = (
                    db.query(
                        ProductPostPublication
                    )
                    .filter(
                        ProductPostPublication.id
                        == publication.id
                    )
                    .first()
                )

                publication.status = "failed"

                publication.error_message = str(e)

                db.commit()

                failed_count += 1

                results.append(
                    {
                        "platform": "instagram",
                        "success": False,
                        "status": "failed",
                        "publication_id": (
                            publication.id
                        ),
                        "error_message": str(e),
                    }
                )

        # ====================================================
        # INSTAGRAM STORY
        # ====================================================

        elif platform == "instagram_story":

            try:

                if instagram_service is None:

                    instagram_service = InstagramService()

                # ------------------------------------------------
                # Publish Instagram Story
                # ------------------------------------------------

                media = (
                    await instagram_service.publish_story(
                        image_url=post.image_url,
                        product_url=post.product_url,
                    )
                )

                if not media.get("success"):

                    raise Exception(
                        str(media)
                    )

                media_id = media.get("media_id")

                if not media_id:

                    raise Exception(
                        "Instagram did not return "
                        "a Story media ID."
                    )

                # ------------------------------------------------
                # Stories currently do not provide the same
                # permalink as normal feed posts.
                # ------------------------------------------------

                platform_post_url = None

                # ------------------------------------------------
                # Update publication
                # ------------------------------------------------

                publication.status = "published"

                publication.platform_post_id = (
                    media_id
                )

                publication.platform_post_url = (
                    platform_post_url
                )

                publication.published_at = (
                    datetime.utcnow()
                )

                publication.error_message = None

                db.commit()
                db.refresh(publication)

                successful_count += 1

                results.append(
                    {
                        "platform": "instagram_story",
                        "success": True,
                        "status": "published",
                        "publication_id": (
                            publication.id
                        ),
                        "platform_post_id": (
                            media_id
                        ),
                        "platform_post_url": (
                            platform_post_url
                        ),
                    }
                )

            except Exception as e:

                db.rollback()

                publication = (
                    db.query(
                        ProductPostPublication
                    )
                    .filter(
                        ProductPostPublication.id
                        == publication.id
                    )
                    .first()
                )

                publication.status = "failed"

                publication.error_message = str(e)

                db.commit()

                failed_count += 1

                results.append(
                    {
                        "platform": "instagram_story",
                        "success": False,
                        "status": "failed",
                        "publication_id": (
                            publication.id
                        ),
                        "error_message": str(e),
                    }
                )

        # ====================================================
        # TIKTOK
        # ====================================================

        elif platform == "tiktok":

            try:

                # ------------------------------------------------
                # Get a valid TikTok access token.
                #
                # TikTokService handles:
                #
                # - Finding the connected account
                # - Checking token expiry
                # - Refreshing the token when necessary
                # ------------------------------------------------

                # ------------------------------------------------
                # Select TikTok account based on authentication.
                #
                # Standalone Social Publisher:
                #   no JWT -> user_id = 1
                #
                # Influencer app:
                #   valid JWT -> authenticated influencer ID
                # ------------------------------------------------

                tiktok_user_id = (
                    int(current_user["id"])
                    if current_user
                    else 1
                )

                access_token = (
                    await TikTokService.get_valid_access_token(
                        user_id=tiktok_user_id
                    )
                )

                if not access_token:

                    raise Exception(
                        "TikTok access token is not available."
                    )

                # ------------------------------------------------
                # Make sure a TikTok-specific JPG exists.
                #
                # Product posts created after the TikTok JPG
                # implementation contain tiktok_jpg_url.
                #
                # Older product posts may not have this value.
                # ------------------------------------------------

                if not post.tiktok_jpg_url:

                    raise Exception(
                        "TikTok JPG image is not available "
                        "for this product post."
                    )

                # ------------------------------------------------
                # Direct Post Photo
                #
                # TikTok uses the separate JPEG generated
                # specifically for TikTok.
                #
                # The original post.image_url remains unchanged
                # and continues to be used by Facebook and
                # Instagram.
                #
                # TikTok uses PULL_FROM_URL.
                # ------------------------------------------------

                tiktok_result = (
                    await TikTokService.direct_post_photo(
                        access_token=access_token,
                        image_url=post.tiktok_jpg_url,
                        title=post.title,
                        description=post.caption,
                        privacy_level="SELF_ONLY",
                    )
                )

                # ------------------------------------------------
                # TikTok returns a publish_id.
                #
                # This is stored in platform_post_id because
                # ProductPostPublication currently provides one
                # platform identifier field.
                # ------------------------------------------------

                publish_id = None

                if isinstance(
                    tiktok_result,
                    dict
                ):

                    publish_id = (
                        tiktok_result.get(
                            "publish_id"
                        )
                    )

                if not publish_id:

                    raise Exception(
                        "TikTok did not return "
                        "a publish_id."
                    )

                # ------------------------------------------------
                # TikTok does not necessarily provide a public
                # permalink from this API response.
                # ------------------------------------------------

                platform_post_url = None

                # ------------------------------------------------
                # Update publication
                # ------------------------------------------------

                publication.status = "published"

                publication.platform_post_id = (
                    publish_id
                )

                publication.platform_post_url = (
                    platform_post_url
                )

                publication.published_at = (
                    datetime.utcnow()
                )

                publication.error_message = None

                db.commit()
                db.refresh(publication)

                successful_count += 1

                results.append(
                    {
                        "platform": "tiktok",
                        "success": True,
                        "status": "published",
                        "publication_id": (
                            publication.id
                        ),
                        "platform_post_id": (
                            publish_id
                        ),
                        "platform_post_url": (
                            platform_post_url
                        ),
                        "tiktok_result": (
                            tiktok_result
                        ),
                    }
                )

            except Exception as e:

                db.rollback()

                publication = (
                    db.query(
                        ProductPostPublication
                    )
                    .filter(
                        ProductPostPublication.id
                        == publication.id
                    )
                    .first()
                )

                publication.status = "failed"

                publication.error_message = str(e)

                db.commit()

                failed_count += 1

                results.append(
                    {
                        "platform": "tiktok",
                        "success": False,
                        "status": "failed",
                        "publication_id": (
                            publication.id
                        ),
                        "error_message": str(e),
                    }
                )

    # ========================================================
    # UPDATE MAIN PRODUCT POST STATUS
    # ========================================================

    if failed_count == 0:

        post.status = "published"

    elif successful_count > 0:

        post.status = "partially_published"

    else:

        post.status = "failed"

    db.commit()
    db.refresh(post)

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "success": (
            successful_count > 0
        ),

        "post": {
            "id": post.id,
            "status": post.status,
        },

        "requested_platforms": platforms,

        "summary": {
            "successful": successful_count,
            "failed": failed_count,
            "total": len(platforms),
        },

        "results": results,
    }