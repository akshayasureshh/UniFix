# import django_filters.rest_framework
# from django_filters import rest_framework as filters
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework import filters
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import UserRegistrationSerializer ,UserSerializer, IssueCreateSerializer, IssueDetailSerializer, IssueListSerializer, CategorySerializer, LocationSerializer, CommentSerializer, IssueUpdateSerializer
from app.models import Issue, Comment, Location, Category
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AuthToken, Upvote, IssueStatusHistory
from rest_framework_simplejwt.views import TokenRefreshView
from .choices import StatusChoices


class AuthViewSet(viewsets.ViewSet):
    def get_tokens_for_user(self, user, device_id):
        refresh = RefreshToken.for_user(user)
        refresh['device_id'] = str(device_id)
        refresh['username'] = user.username
        refresh['role'] = user.role
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                device_id = request.data.get('device_id')
                tokens = self.get_tokens_for_user(user, device_id)
                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': tokens,
                    'device_id': str(device_id)
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        device_id = request.data.get('device_id')
        if not device_id:
            return Response(
                {'error': 'device_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        if user:
            token_obj, created = AuthToken.objects.get_or_create(
                user=user,
                device_id=device_id
            )
            tokens = self.get_tokens_for_user(user, device_id)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': tokens,
                'device_id': str(device_id)
            })
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def refresh(self, request):
        refresh_view = TokenRefreshView.as_view()
        return refresh_view(request._request)
    


    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def devices(self, request):
        """List all devices for the current user"""
        devices = AuthToken.objects.filter(user=request.user, status=True)
        data = [{
            'device_id': str(d.device_id),
            'device_name': d.device_name,
            'last_login': d.last_login,
            'created_at': d.created_at,
        } for d in devices]
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def revoke_device(self, request):
        """Revoke/remove a device"""
        device_id = request.data.get('device_id')
        if not device_id:
            return Response({'error': 'device_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = AuthToken.objects.get(user=request.user, device_id=device_id)
            token.status = False
            token.save()
            return Response({'message': 'Device revoked successfully'})
        except AuthToken.DoesNotExist:
            return Response({'error': 'Device not found'}, status=status.HTTP_404_NOT_FOUND)

class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'location']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'upvotes_count', 'priority']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return IssueCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return IssueUpdateSerializer
        elif self.action == 'list':
            return IssueListSerializer
        return IssueDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
    
    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        issue = self.get_object()
        upvote, created = Upvote.objects.get_or_create(
            user=request.user, 
            issue=issue
        )
        if created:
            issue.upvotes_count += 1
            issue.save()
            return Response({'message': 'Issue upvoted'})
        else:
            upvote.delete()
            issue.upvotes_count -= 1
            issue.save()
            return Response({'message': 'Upvote removed'})
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        issue = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(author=request.user, issue=issue)
            issue.comments_count += 1
            issue.save()
            return Response(CommentSerializer(comment).data, 
                          status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_status(self, request, pk=None):
        issue = self.get_object()
        if request.user.role not in ['admin', 'staff', 'maintenance']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        new_status = request.data.get('status')
        old_status = issue.status
        if new_status not in StatusChoices.values:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        IssueStatusHistory.objects.create(
            issue=issue,
            changed_by=request.user,
            old_status=old_status,
            new_status=new_status,
            comment=request.data.get('comment', '')
        )
        issue.status = new_status
        if new_status == StatusChoices.RESOLVED:
            issue.resolved_at = timezone.now()
        issue.save()
        return Response(
            {'message': f'Status updated successfully to {new_status}'},
            status=status.HTTP_200_OK
        )
        

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.filter(is_active=True)
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        issue_id = self.kwargs.get('issue_pk')
        if issue_id:
            return Comment.objects.filter(issue_id=issue_id)
        return Comment.objects.all()
    
    def perform_create(self, serializer):
        issue_id = self.request.data.get('issue')
        serializer.save(author=self.request.user, issue_id=issue_id)