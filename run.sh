#python3 `which gunicorn` -k flask_sockets.worker sockets:app

gunicorn -k flask_sockets.worker sockets:app
