import os
import django
import sys

# Current directory is already in sys.path when running via python command
# e:\FoodOyes\Trilobe_Main\TrilobeMain
# sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.properties.serializers import HotelDetailSerializer, HomestayDetailSerializer
from api.packages.serializers import HolidayPackageDetailSerializer
from api.houseboats.serializers import HouseBoatDetailSerializer
from api.activities.serializers import ActivityDetailSerializer

print("All serializers imported successfully.")
