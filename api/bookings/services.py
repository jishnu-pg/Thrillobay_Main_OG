from decimal import Decimal
from django.utils import timezone
from apps.bookings.models import BookingItem
from apps.properties.models import Property, RoomType, RoomOption
from apps.packages.models import HolidayPackage
from apps.activities.models import Activity
from apps.cabs.models import Cab, CabPricingOption
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
    def calculate_pricing(booking_type, items_data, check_in, check_out, coupon_code=None, is_insurance_opted=False):
        total_base_price = Decimal(0)
        total_tax_amount = Decimal(0)
        breakdown = []
        
        nights = (check_out - check_in).days
        if nights < 1:
            nights = 1

        for item in items_data:
            item_price = Decimal(0)
            item_tax = Decimal(0)
            item_details = {}
            
            if booking_type == "stay":
                room_type_id = item.get("room_type_id")
                room_option_id = item.get("room_option_id")
                quantity = item.get("quantity", 1)
                room_type = RoomType.objects.get(id=room_type_id)
                
                if room_option_id:
                    room_option = RoomOption.objects.get(id=room_option_id)
                    price_per_night = room_option.discounted_price + room_option.gst_amount
                    base_price_per_night = room_option.discounted_price
                    tax_per_night = room_option.gst_amount
                    item_name = f"{room_type.name} - {room_option.name}"
                else:
                    price_per_night = room_type.total_payable_amount
                    base_price_per_night = room_type.discounted_price
                    tax_per_night = room_type.gst_amount
                    item_name = room_type.name

                item_total_inc_tax = price_per_night * nights * quantity
                item_total_base = base_price_per_night * nights * quantity
                item_total_tax = tax_per_night * nights * quantity
                
                item_details = {
                    "name": item_name,
                    "sub_name": room_type.property.name,
                    "location": f"{room_type.property.city}, {room_type.property.state}",
                    "quantity": quantity,
                    "nights": nights,
                    "price_per_unit": price_per_night,
                    "total": item_total_inc_tax,
                    "image": BookingPricingService._get_image(room_type, "stay")
                }
                
                total_base_price += item_total_base
                total_tax_amount += item_total_tax

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
                
                # Apply 18% GST for packages
                gst_rate = Decimal("0.18")
                item_tax = item_price * gst_rate
                
                item_details = {
                    "name": package.title,
                    "sub_name": f"{package.duration_nights} Nights / {package.duration_days} Days",
                    "location": package.primary_location,
                    "adults": adults,
                    "children": children,
                    "price_per_person": price_per_person,
                    "total": item_price + item_tax,
                    "image": BookingPricingService._get_image(package, "package")
                }
                
                total_base_price += item_price
                total_tax_amount += item_tax

            elif booking_type == "activity":
                activity_id = item.get("activity_id")
                adults = item.get("adults", 1)
                children = item.get("children", 0)
                activity = Activity.objects.get(id=activity_id)
                
                pricing = activity.calculate_pricing()
                price_per_person = Decimal(str(pricing["discounted_price"]))
                base_price_per_person = Decimal(str(pricing["base_price"]))
                
                total_pax = adults + children
                item_price = price_per_person * total_pax
                
                # Apply 18% GST for activities
                gst_rate = Decimal("0.18")
                item_tax = item_price * gst_rate
                
                # Get Features (Icons)
                features = []
                for feature in activity.features.filter(is_included=True):
                    features.append({
                        "name": feature.get_feature_type_display(),
                        "type": feature.feature_type,
                        "is_included": True
                    })
                
                # Get Inclusions (List)
                inclusions = []
                for inc in activity.inclusions.all():
                    inclusions.append({
                        "name": inc.text,
                        "is_included": inc.is_included
                    })

                duration_str = f"{activity.duration_days} Days"
                if activity.duration_nights > 0:
                    duration_str += f" / {activity.duration_nights} Nights"

                item_details = {
                    "name": activity.title,
                    "sub_name": f"{duration_str} | {activity.get_difficulty_display()}",
                    "location": activity.location,
                    "duration": duration_str,
                    "adults": adults,
                    "children": children,
                    "price_per_person": price_per_person,
                    "base_price_per_person": base_price_per_person,
                    "total": item_price + item_tax,
                    "image": BookingPricingService._get_image(activity, "activity"),
                    "features": features,
                    "inclusions": inclusions
                }
                
                total_base_price += item_price
                total_tax_amount += item_tax
            
            elif booking_type == "cab":
                cab_id = item.get("cab_id")
                quantity = item.get("quantity", 1)
                cab = Cab.objects.get(id=cab_id)
                
                # Pricing Logic
                # Use base_price as the full payment amount for now (Airport Transfer/Flat Rate)
                full_price = cab.base_price
                
                # Check for pricing options (Part Payment vs Full Payment)
                pricing_opts = CabPricingOption.objects.filter(cab=cab)
                payment_options = []
                
                # Default Full Payment
                payment_options.append({
                    "label": "Make full payment now",
                    "value": "full",
                    "amount": full_price,
                    "is_default": True
                })
                
                # Check for Part Payment option
                part_pay_opt = pricing_opts.filter(option_type="pay_now").first()
                if part_pay_opt:
                    payment_options.append({
                        "label": "Make part payment now",
                        "value": "part",
                        "amount": part_pay_opt.amount,
                        "description": f"Pay the rest to the driver"
                    })
                else:
                    # Default part payment (e.g. 10%) if not explicitly defined
                    part_amount = (full_price * Decimal("0.10")).quantize(Decimal("1.00"))
                    payment_options.append({
                        "label": "Make part payment now",
                        "value": "part",
                        "amount": part_amount,
                        "description": "Pay the rest to the driver"
                    })

                item_price = full_price * quantity
                
                # Apply 18% GST for cabs
                gst_rate = Decimal("0.18")
                item_tax = item_price * gst_rate
                
                # Get Inclusions
                inclusions = []
                for inc in cab.inclusions.all():
                    inclusions.append({
                        "name": inc.label,
                        "value": inc.value,
                        "is_included": inc.is_included
                    })

                item_details = {
                    "name": cab.title,
                    "sub_name": cab.category.name if cab.category else "",
                    "location": item.get("pickup_location", "Cab Service"),
                    "pickup_location": item.get("pickup_location"),
                    "drop_location": item.get("drop_location"),
                    "quantity": quantity,
                    "pickup_datetime": item.get("pickup_datetime"),
                    "trip_type": item.get("trip_type"),
                    "price_per_unit": full_price,
                    "total": item_price + item_tax,
                    "image": BookingPricingService._get_image(cab, "cab"),
                    "payment_options": payment_options,
                    "inclusions": inclusions
                }
                
                total_base_price += item_price
                total_tax_amount += item_tax

            elif booking_type == "houseboat":
                houseboat_id = item.get("houseboat_id")
                quantity = item.get("quantity", 1)
                houseboat = HouseBoat.objects.get(id=houseboat_id)
                
                pricing = houseboat.calculate_pricing()
                price_per_night = Decimal(str(pricing["discounted_price"]))
                
                # Check for Extra Guests
                extra_guest_total = Decimal(0)
                # Assume standard capacity is bedrooms * 2 (common for houseboats)
                standard_capacity = 0
                if hasattr(houseboat, 'specification'):
                    standard_capacity = houseboat.specification.bedrooms * 2
                else:
                    standard_capacity = 2 # Fallback
                
                adults = item.get("adults", 2)
                children = item.get("children", 0)
                total_pax = adults + children
                
                if total_pax > standard_capacity:
                    # Calculate extra pax
                    # Priority: Adults fill standard capacity first
                    remaining_capacity = standard_capacity
                    
                    # Fill with adults
                    adults_in_base = min(adults, remaining_capacity)
                    remaining_capacity -= adults_in_base
                    extra_adults = adults - adults_in_base
                    
                    # Fill with children
                    children_in_base = min(children, remaining_capacity)
                    extra_children = children - children_in_base
                    
                    extra_guest_total += (Decimal(extra_adults) * houseboat.extra_guest_price_adult)
                    extra_guest_total += (Decimal(extra_children) * houseboat.extra_guest_price_child)

                # Check for Full Time AC
                ac_total = Decimal(0)
                is_ac_opted = item.get("is_full_time_ac_opted", False)
                if is_ac_opted:
                     ac_total = houseboat.full_time_ac_price

                # Total Per Night = Base Price + Extra Guests + AC
                nightly_total = price_per_night + extra_guest_total + ac_total
                
                item_price = nightly_total * quantity * nights
                
                # Apply 18% GST for houseboats
                gst_rate = Decimal("0.18")
                item_tax = item_price * gst_rate
                
                item_details = {
                    "name": houseboat.name,
                    "sub_name": f"{houseboat.specification.bedrooms} BHK" if hasattr(houseboat, 'specification') else "",
                    "location": houseboat.location,
                    "quantity": quantity,
                    "nights": nights,
                    "price_per_unit": price_per_night,
                    "extra_guest_price": extra_guest_total,
                    "ac_price": ac_total,
                    "total": item_price + item_tax,
                    "image": BookingPricingService._get_image(houseboat, "houseboat")
                }
                
                total_base_price += item_price
                total_tax_amount += item_tax
            
            breakdown.append(item_details)

        # Coupon Logic
        coupon_discount = Decimal(0)
        coupon_applied = None
        
        gross_total = total_base_price + total_tax_amount
        
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, valid_from__lte=timezone.now().date(), valid_to__gte=timezone.now().date())
                coupon_discount = coupon.discount_amount
                
                if coupon_discount > gross_total:
                    coupon_discount = gross_total
                    
                coupon_applied = {
                    "code": coupon.code,
                    "discount_amount": coupon_discount
                }
            except Coupon.DoesNotExist:
                pass

        # Insurance Logic
        insurance_fee = Decimal(0)
        if is_insurance_opted:
            insurance_fee = Decimal("600.00")

        final_total = gross_total - coupon_discount + insurance_fee

        return {
            "breakdown": breakdown,
            "base_total": total_base_price,
            "taxes": total_tax_amount,
            "coupon_discount": coupon_discount,
            "insurance_fee": insurance_fee,
            "coupon_applied": coupon_applied,
            "final_total": final_total
        }
