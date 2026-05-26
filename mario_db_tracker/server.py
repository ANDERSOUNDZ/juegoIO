from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n[SERVER] Abre http://localhost:5000 en tu navegador")
    print("[SERVER] La camara se activa en el CLIENTE (navegador)")
    print("[SERVER] Presiona Ctrl+C para detener\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
