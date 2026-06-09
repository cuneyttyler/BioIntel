import os

from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import RagDocument
from core.serializers import RagDocumentSerializer
from core.services import rag as rag_service


class RagDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = RagDocumentSerializer

    def get_queryset(self):
        qs = RagDocument.objects.all().order_by('-created_at')
        project_id = self.request.query_params.get('project_id')
        if project_id:
            qs = qs.filter(project_id=project_id)
        doc_type = self.request.query_params.get('document_type')
        if doc_type:
            qs = qs.filter(document_type=doc_type)
        name = self.request.query_params.get('name')
        if name:
            qs = qs.filter(name__icontains=name)
        return qs

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'file required'}, status=400)

        upload_dir = os.path.join(str(settings.MEDIA_ROOT), 'rag_documents')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, uploaded_file.name)

        with open(file_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        doc = RagDocument.objects.create(
            name=request.data.get('name', os.path.splitext(uploaded_file.name)[0]),
            document_type=request.data.get('document_type', 'other'),
            molecule_type=request.data.get('molecule_type', 'both'),
            phase_relevance=request.data.getlist('phase_relevance', []),
            file_path=file_path,
            project_id=request.data.get('project_id') or None,
            uploaded_by=request.data.get('uploaded_by', 'scientist'),
        )

        # Trigger ingestion synchronously (in production, use Celery)
        rag_service.ingest_document(doc.id)
        doc.refresh_from_db()

        return Response(RagDocumentSerializer(doc).data, status=201)


class RagDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RagDocument.objects.all()
    serializer_class = RagDocumentSerializer
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']


class RagDocumentIngestView(APIView):
    """POST /api/documents/<pk>/ingest/ — trigger re-ingestion."""

    def post(self, request, pk):
        try:
            doc = RagDocument.objects.get(pk=pk)
        except RagDocument.DoesNotExist:
            return Response({'error': 'Document not found'}, status=404)

        success = rag_service.ingest_document(doc.id)
        doc.refresh_from_db()
        return Response({
            'status': doc.ingestion_status,
            'chunk_count': doc.chunks.count(),
        })


class RagDocumentSearchView(APIView):
    """GET /api/documents/search/?q=query&phase=...&molecule_type=...&project_id=..."""

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'error': 'q parameter required'}, status=400)

        phase = request.query_params.get('phase') or None
        molecule_type = request.query_params.get('molecule_type') or None
        project_id = request.query_params.get('project_id') or None
        if project_id:
            project_id = int(project_id)

        chunks = rag_service.retrieve(
            query=query,
            phase=phase,
            molecule_type=molecule_type,
            project_id=project_id,
        )

        return Response({'results': chunks, 'query': query})
