# views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework import filters
from .serializers import UserRegistrationSerializer ,UserSerializer, IssueCreateSerializer, IssueDetailSerializer, IssueListSerializer, CategorySerializer, LocationSerializer, CommentSerializer
from app.models import Issue, Comment, Location, Category
from django_filters.rest_framework import DjangoFilterBackend

class AuthViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key
            })
        return Response({'error': 'Invalid credentials'}, 
                       status=status.HTTP_401_UNAUTHORIZED)


class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'location']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'upvotes_count', 'priority']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return IssueCreateSerializer
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
    
    @action(detail=True, methods=['patch'], 
            permission_classes=[permissions.IsAuthenticated])
    def update_status(self, request, pk=None):
        issue = self.get_object()
        
        if request.user.role not in ['admin', 'staff', 'maintenance']:
            return Response({'error': 'Permission denied'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        new_status = request.data.get('status')
        old_status = issue.status
        
        if new_status in dict(Issue.STATUS_CHOICES):
            # Create status history
            IssueStatusHistory.objects.create(
                issue=issue,
                changed_by=request.user,
                old_status=old_status,
                new_status=new_status,
                comment=request.data.get('comment', '')
            )
            
            issue.status = new_status
            if new_status == 'resolved':
                issue.resolved_at = timezone.now()
            issue.save()
            
            return Response({'message': 'Status updated successfully'})
        
        return Response({'error': 'Invalid status'}, 
                       status=status.HTTP_400_BAD_REQUEST)
        

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.filter(is_active=True)
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)