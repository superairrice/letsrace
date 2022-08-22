from rest_framework.serializers import ModelSerializer
from base.models import Room


class RoomSerializer(ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

        # model = Room
        # fields = '__all__'    # 전체 컬럼 불러오기
        # exclude = ['host', 'participants']
