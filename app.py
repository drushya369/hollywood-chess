import os
import random
from flask import Flask, render_template, jsonify, request
import chess

app = Flask(__name__)

# In-memory storage for game state
game_board = chess.Board()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "fen": game_board.fen(),
        "is_game_over": game_board.is_game_over(),
        "turn": "white" if game_board.turn == chess.WHITE else "black"
    })

@app.route('/api/moves', methods=['GET'])
def get_valid_moves():
    # Returns legal moves for the selected square
    square_str = request.args.get('square', '')
    if not square_str:
        return jsonify({"moves": []})
    
    try:
        square = chess.parse_square(square_str)
        moves = [m.uci() for m in game_board.legal_moves if m.from_square == square]
        return jsonify({"moves": moves})
    except ValueError:
        return jsonify({"error": "Invalid square"}, 400)

@app.route('/api/move', methods=['POST'])
def make_move():
    data = request.get_json()
    move_uci = data.get('move')
    
    try:
        move = chess.Move.from_uci(move_uci)
        if move in game_board.legal_moves:
            is_capture = game_board.is_capture(move)
            game_board.push(move)
            
            response = {
                "success": True,
                "fen": game_board.fen(),
                "is_capture": is_capture,
                "game_over": game_board.is_game_over()
            }
            return jsonify(response)
        else:
            return jsonify({"success": False, "error": "Illegal Move"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/ai_move', methods=['POST'])
def ai_move():
    if game_board.is_game_over():
        return jsonify({"success": False, "error": "Game Over"})
    
    # Simple AI: Evaluates captures first, otherwise picks a random legal move
    legal_moves = list(game_board.legal_moves)
    captures = [m for m in legal_moves if game_board.is_capture(m)]
    
    chosen_move = random.choice(captures) if captures else random.choice(legal_moves)
    is_capture = game_board.is_capture(chosen_move)
    game_board.push(chosen_move)
    
    return jsonify({
        "success": True,
        "move": chosen_move.uci(),
        "fen": game_board.fen(),
        "is_capture": is_capture,
        "game_over": game_board.is_game_over()
    })

@app.route('/api/reset', methods=['POST'])
def reset_game():
    global game_board
    game_board = chess.Board()
    return jsonify({"success": True, "fen": game_board.fen()})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
