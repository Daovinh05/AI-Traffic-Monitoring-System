"""
API Routes - Xử lý các endpoint API
"""
from flask import Blueprint, request, jsonify, send_file
import os

api = Blueprint('api', __name__)

# Import services
from services.ai_service import (
    call_groq_law_advisor,
    process_ai_chat_message,
    warnings
)


@api.route('/api/groq_law_chat', methods=['POST'])
def api_groq_law_chat():
    """API tư vấn luật giao thông bằng Groq AI"""
    try:
        data = request.get_json()
        message = data.get('message', '')

        print(f"[LAW CHAT] User hỏi: {message}")

        # Gọi Groq API để tư vấn luật
        response = call_groq_law_advisor(message)

        return jsonify({
            'status': 'success',
            'response': response
        })

    except Exception as e:
        print(f"Lỗi api_groq_law_chat: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


@api.route('/api/send_chat_message', methods=['POST'])
def api_send_chat_message():
    """API gửi tin nhắn vào chatbot với AI xử lý"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        vehicle_id = data.get('vehicle_id')
        user_id = data.get('user_id', 'anonymous')

        # Lưu tin nhắn vào database (nếu có)
        print(f"[CHAT] User {user_id} (xe {vehicle_id}): {message}")

        # AI xử lý và tạo phản hồi
        bot_response = process_ai_chat_message(message, vehicle_id)

        return jsonify({
            'status': 'success',
            'bot_response': bot_response
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


@api.route('/api/get_ai_warnings')
def api_get_ai_warnings():
    """API để frontend lấy cảnh báo AI hiện tại"""
    return jsonify(warnings)


@api.route('/get_warnings')
def get_warnings():
    """Lấy cảnh báo AI (legacy route)"""
    return jsonify(warnings)
