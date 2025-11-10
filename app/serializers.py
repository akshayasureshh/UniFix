from rest_framework import serializers
from .models import *


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    device_id = serializers.UUIDField(write_only=True, required=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        device_id = validated_data.pop('device_id')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        AuthToken.objects.create(user=user, device_id=device_id)
        return user
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                    'first_name', 'last_name', 'role', 'student_id', 
                'department', 'device_id']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'department', 'is_verified', 'profile_picture']
        read_only_fields = ['id']
        
        
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class IssueImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueImage
        fields = ['id', 'image', 'caption']

class IssueListSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    is_upvoted = serializers.SerializerMethodField()
    
    class Meta:
        model = Issue
        fields = ['id', 'title', 'description', 'reporter', 'category', 
                 'location', 'priority', 'status', 'upvotes_count', 
                 'comments_count', 'created_at', 'is_upvoted']
    
    def get_is_upvoted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.upvotes.filter(user=request.user).exists()
        return False

class IssueDetailSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    images = IssueImageSerializer(many=True, read_only=True)
    is_upvoted = serializers.SerializerMethodField()
    
    class Meta:
        model = Issue
        fields = '__all__'
    
    def get_is_upvoted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.upvotes.filter(user=request.user).exists()
        return False

class IssueCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(), 
        required=False, 
        write_only=True
    )
    
    def validate(self, data):
        if 'location' not in data or data['location'] is None:
            raise serializers.ValidationError("Location is required")
        return data
  
    def create(self, validated_data):
        print("validated_date", validated_data)
        images_data = validated_data.pop('images', [])
        issue = Issue.objects.create(**validated_data)
        print(issue)
        for image_data in images_data:
            IssueImage.objects.create(issue=issue, image=image_data)
        return issue
    
    class Meta:
        model = Issue
        fields = ['id', 'title', 'description', 'category', 'location', 'is_anonymous', 'images']

    

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'issue', 'author', 'parent', 'created_at', 
                 'updated_at', 'is_edited', 'replies']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at', 'is_edited']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True, context=self.context).data
        return []

class UpvoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upvote
        fields = ['id', 'created_at']
        read_only_fields = ['id', 'created_at']