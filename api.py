"""
KREPS RAG System - Flask API Server
Exposes HTTP endpoints for frontend integration
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from rag import QwenRAGSystem
from werkzeug.utils import secure_filename
import os
import traceback
from chunk import process_document

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

rag_system = QwenRAGSystem(
    collection_name="kreps_documents",
    ollama_model="qwen2.5:14b",
    top_k=5,
    auto_cleanup=True
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'KREPS RAG System API',
        'version': '1.0',
        'endpoints': {
            'GET /': 'API information',
            'GET /health': 'Health check',
            'POST /query': 'Answer questions',
            'POST /upload': 'Upload documents',
            'GET /stats': 'Database statistics',
            'GET /documents': 'List documents'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    try:
        health_status = rag_system.health_check()
        return jsonify(health_status), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/query', methods=['POST'])
def query():
    try:
        data = request.json

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        user_query = data.get('query', '')

        if not user_query or not user_query.strip():
            return jsonify({'error': 'Query is required and cannot be empty'}), 400

        result = rag_system.answer_query(user_query)
        return jsonify(result), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'query': data.get('query', '') if data else ''}), 500


@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')

        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        saved_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                saved_files.append(filename)

        if not saved_files:
            return jsonify({'error': 'No valid files uploaded. Only PDF and TXT files are allowed.'}), 400

        all_chunks = []
        for filename in saved_files:
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            chunks = process_document(filepath, chunk_size=500, chunk_overlap=100)
            all_chunks.extend(chunks)

        if all_chunks:
            texts = [c.page_content for c in all_chunks]
            embeddings = rag_system.embedding_module.embed_documents(texts)
            rag_system.vector_db.store_chunks_with_embeddings(all_chunks, embeddings)

        return jsonify({
            'success': True,
            'files_processed': len(saved_files),
            'files': saved_files,
            'message': f'{len(saved_files)} document(s) uploaded successfully'
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def stats():
    try:
        stats = rag_system.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/documents', methods=['GET'])
def list_documents():
    try:
        stats = rag_system.get_stats()
        return jsonify({
            'documents': stats.get('document_names', []),
            'total': stats.get('unique_documents', 0)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
