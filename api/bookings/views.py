from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import BookingCreateSerializer, BookingListSerializer, BookingDetailSerializer, BookingConfirmSerializer
from apps.bookings.models import Booking
from apps.coupons.models import Coupon
from .services import BookingPricingService

class BookingCreateAPIView(CreateAPIView):
    """
    API to create a new booking for Homestays/Villas/Hotels.
    Handles 'Entire Place' vs 'Individual Rooms' logic automatically.
    """
    serializer_class = BookingCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # The create method in serializer uses self.context['request'].user
        serializer.save()

class BookingReviewAPIView(APIView):
    """
    API to review booking details, create a draft booking, and get pricing breakdown.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Use BookingCreateSerializer to validate and create draft booking
        serializer = BookingCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Extract data for pricing service BEFORE save, as save() might pop fields
        check_in = serializer.validated_data.get("check_in")
        check_out = serializer.validated_data.get("check_out")
        items_data = request.data.get("items")
        coupon_code = request.data.get("coupon_code")
        
        # Save as draft
        booking = serializer.save(status='draft')
        
        pricing_data = BookingPricingService.calculate_pricing(
            booking_type=booking.booking_type,
            items_data=items_data,
            check_in=check_in,
            check_out=check_out,
            coupon_code=coupon_code,
            is_insurance_opted=booking.is_insurance_opted
        )
        
        # Update booking total amount with the final calculated total (including taxes/coupons)
        booking.total_amount = pricing_data["final_total"]
        booking.insurance_amount = pricing_data["insurance_fee"]
        booking.save()
        
        # Prepare response (Only return booking_id as requested)
        return Response({
            "booking_id": booking.id,
            "message": "Booking review created successfully."
        })

    def get(self, request, *args, **kwargs):
        """
        Retrieve review details for an existing draft booking using booking_id query param.
        """
        booking_id = request.query_params.get("booking_id")
        if not booking_id:
            return Response({"error": "booking_id is required"}, status=400)
        
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        
        # Ensure we only review draft bookings
        if booking.status != 'draft':
            return Response({"error": "Only draft bookings can be reviewed."}, status=400)
            
        # Reconstruct inputs for Pricing Service
        items_data = []
        check_in = None
        check_out = None
        
        # Group similar items if needed, but for now we just list them
        # Note: quantity is implicitly handled because multiple BookingItem rows exist for quantity > 1
        # But BookingPricingService iterates and multiplies by quantity.
        # So we should treat each BookingItem as quantity=1
        
        for item in booking.items.all():
            # Capture check_in/check_out from the first item (should be same for all in a booking)
            if check_in is None:
                check_in = item.check_in
                check_out = item.check_out
            
            item_dict = {
                "quantity": 1,
                "adults": item.adults,
                "children": item.children
            }
            
            if booking.booking_type == "stay" and item.room_type:
                item_dict["room_type_id"] = item.room_type.id
            elif booking.booking_type == "package" and item.package:
                item_dict["package_id"] = item.package.id
            elif booking.booking_type == "activity" and item.activity:
                item_dict["activity_id"] = item.activity.id
            elif booking.booking_type == "cab" and item.cab:
                item_dict["cab_id"] = item.cab.id
                item_dict["pickup_location"] = item.pickup_location
                item_dict["drop_location"] = item.drop_location
                item_dict["pickup_datetime"] = item.pickup_datetime
                item_dict["trip_type"] = item.trip_type
            elif booking.booking_type == "houseboat" and item.houseboat:
                item_dict["houseboat_id"] = item.houseboat.id
                
            items_data.append(item_dict)
            
        # Retrieve applied coupon if stored
        coupon_code = None 
        if booking.coupon:
            coupon_code = booking.coupon.code
        
        pricing_data = BookingPricingService.calculate_pricing(
            booking_type=booking.booking_type,
            items_data=items_data,
            check_in=check_in,
            check_out=check_out,
            coupon_code=coupon_code,
            is_insurance_opted=booking.is_insurance_opted
        )
        
        # Prepare response
        response_data = pricing_data
        response_data["booking_id"] = booking.id
        response_data["check_in"] = check_in
        response_data["check_out"] = check_out
        
        return Response(response_data)

class BookingConfirmAPIView(UpdateAPIView):
    """
    API to confirm a draft booking by adding traveller details and updating status.
    """
    serializer_class = BookingConfirmSerializer
    permission_classes = [IsAuthenticated]
    queryset = Booking.objects.all()
    lookup_field = "id"

    def get_queryset(self):
        # Ensure user can only confirm their own draft bookings
        return Booking.objects.filter(user=self.request.user, status="draft")

    def update(self, request, *args, **kwargs):
        # We override update to provide a custom response
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            "message": "Booking confirmed successfully.", 
            "booking_id": instance.id,
            "status": instance.status
        })

class BookingListAPIView(ListAPIView):
    """
    API to list all bookings for the authenticated user.
    Supports filtering by status: 'upcoming', 'cancelled', 'completed'.
    Ordered by most recent first.
    """
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Booking.objects.filter(user=self.request.user)
        status_param = self.request.query_params.get("status")
        
        if status_param == "upcoming":
             # upcoming includes pending and confirmed bookings
             queryset = queryset.filter(status__in=["pending", "confirmed"])
        elif status_param == "cancelled":
             queryset = queryset.filter(status="cancelled")
        elif status_param == "completed":
             queryset = queryset.filter(status="completed")
             
        return queryset.order_by("-created_at")

class BookingDetailAPIView(RetrieveAPIView):
    """
    API to get full details of a specific booking.
    Ensures user can only see their own bookings.
    """
    serializer_class = BookingDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
