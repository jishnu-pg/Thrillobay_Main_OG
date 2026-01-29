from decimal import Decimal
from django.utils import timezone
from apps.bookings.models import BookingItem
from apps.properties.models import Property, RoomType
from apps.packages.models import HolidayPackage
from apps.activities.models import Activity
from apps.cabs.models import Cab
from apps.houseboats.models import HouseBoat
from apps.coupons.models import Coupon

class BookingPricingService:
    @staticmethod
    def _get_image(obj, obj_type):
        image_url = None
        if obj_type == "stay":
            # RoomType -> Property -> Image
            if obj.property.primary_image:
                image_url = obj.property.primary_image.image.url
        elif obj_type == "package":
            img = obj.images.filter(is_primary=True).first() or obj.images.first()
            if img: image_url = img.image.url
        elif obj_type == "activity":
            img = obj.images.filter(is_primary=True).first() or obj.images.first()
            if img: image_url = img.image.url
        elif obj_type == "cab":
            img = obj.images.filter(is_primary=True).first() or obj.images.first()
            if img: image_url = img.image.url
        elif obj_type == "houseboat":
            img = obj.images.filter(is_primary=True).first() or obj.images.first()
            if img: image_url = img.image.url
        
        return image_url

    @staticmethod
    def calculate_pricing(booking_type, items_data, check_in, check_out, coupon_code=None):
        total_base_price = Decimal(0)
        breakdown = []
        
        nights = (check_out - check_in).days
        if nights < 1:
            nights = 1

        for item in items_data:
            item_price = Decimal(0)
            item_details = {}
            
            if booking_type == "stay":
                room_type_id = item.get("room_type_id")
                quantity = item.get("quantity", 1)
                room_type = RoomType.objects.get(id=room_type_id)
                
                price_per_night = room_type.total_payable_amount
                item_price = price_per_night * nights * quantity
                
                item_details = {
                    "name": room_type.name,
                    "sub_name": room_type.property.name,
                    "location": f"{room_type.property.city}, {room_type.property.state}",
                    "quantity": quantity,
                    "nights": nights,
                    "price_per_unit": price_per_night,
                    "total": item_price,
                    "image": BookingPricingService._get_image(room_type, "stay")
                }

            elif booking_type == "package":
                package_id = item.get("package_id")
                adults = item.get("adults", 1)
                children = item.get("children", 0)
                package = HolidayPackage.objects.get(id=package_id)
                
                price_per_person = package.base_price
                if package.discount and package.discount.is_active:
                     if package.discount.discount_type == "percentage":
                         price_per_person = price_per_person - (price_per_person * package.discount.value / 100)
                     else:
                         price_per_person = price_per_person - package.discount.value
                
                total_pax = adults + children
                item_price = price_per_person * total_pax
                
                item_details = {
                    "name": package.title,
                    "sub_name": f"{package.duration_nights} Nights / {package.duration_days} Days",
                    "location": package.primary_location,
                    "adults": adults,
                    "children": children,
                    "price_per_person": price_per_person,
                    "total": item_price,
                    "image": BookingPricingService._get_image(package, "package")
                }

            elif booking_type == "activity":
                activity_id = item.get("activity_id")
                adults = item.get("adults", 1)
                children = item.get("children", 0)
                activity = Activity.objects.get(id=activity_id)
                
                pricing = activity.calculate_pricing()
                price_per_person = Decimal(str(pricing["discounted_price"]))
                
                total_pax = adults + children
                item_price = price_per_person * total_pax
                
                item_details = {
                    "name": activity.title,
                    "sub_name": activity.get_difficulty_display(),
                    "location": activity.location,
                    "adults": adults,
                    "children": children,
                    "price_per_person": price_per_person,
                    "total": item_price,
                    "image": BookingPricingService._get_image(activity, "activity")
                }
            
            elif booking_type == "cab":
                cab_id = item.get("cab_id")
                quantity = item.get("quantity", 1)
                cab = Cab.objects.get(id=cab_id)
                
                price_per_day = cab.base_price
                item_price = price_per_day * quantity * nights
                
                item_details = {
                    "name": cab.title,
                    "sub_name": cab.category.name if cab.category else "",
                    "location": "Cab Service", # Cabs might not have a fixed location in the same way
                    "quantity": quantity,
                    "nights": nights,
                    "price_per_unit": price_per_day,
                    "total": item_price,
                    "image": BookingPricingService._get_image(cab, "cab")
                }

            elif booking_type == "houseboat":
                houseboat_id = item.get("houseboat_id")
                quantity = item.get("quantity", 1)
                houseboat = HouseBoat.objects.get(id=houseboat_id)
                
                pricing = houseboat.calculate_pricing()
                price_per_night = Decimal(str(pricing["discounted_price"]))
                
                item_price = price_per_night * quantity * nights
                
                item_details = {
                    "name": houseboat.name,
                    "sub_name": f"{houseboat.specification.bedrooms} BHK" if hasattr(houseboat, 'specification') else "",
                    "location": houseboat.location,
                    "quantity": quantity,
                    "nights": nights,
                    "price_per_unit": price_per_night,
                    "total": item_price,
                    "image": BookingPricingService._get_image(houseboat, "houseboat")
                }
            
            total_base_price += item_price
            breakdown.append(item_details)

        # Taxes (18% GST)
        gst_rate = Decimal("0.18")
        
        gst_amount = total_base_price * gst_rate
        
        # Coupon Logic
        coupon_discount = Decimal(0)
        coupon_applied = None
        
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, valid_from__lte=timezone.now().date(), valid_to__gte=timezone.now().date())
                coupon_discount = coupon.discount_amount
                
                if coupon_discount > total_base_price:
                    coupon_discount = total_base_price
                    
                coupon_applied = {
                    "code": coupon.code,
                    "discount_amount": coupon_discount
                }
            except Coupon.DoesNotExist:
                pass

        final_total = total_base_price + gst_amount - coupon_discount

        return {
            "breakdown": breakdown,
            "base_total": total_base_price,
            "taxes": gst_amount,
            "coupon_discount": coupon_discount,
            "coupon_applied": coupon_applied,
            "final_total": final_total
        }
