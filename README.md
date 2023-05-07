# smart-bike-rack-polito

Bicycle users of Politecnico di Torino are growing any year, they spent valuable time trying to find free spots at the campus' bike racks, as an answer to this need, this project involves the design and control of a prototype smart bike rack system, which helps users find free parking spots within Politecnico di Torino. 

The system provides real-time updates on the status of one of the university’s racks and predicts its state for the next hour and a half. A camera and Raspberry Pi system are used to capture real-time images, and they communicate via API with a MongoDB database. Additionally, the Big Data Polito cluster server communicates with the database through the SSH protocol, enabling the execution of YOLO-based bike detection code and Random Forest-based state forecasting. Finally, a Telegram bot serves as the user interface.

Team: Ayala Gil, Alejandro; Mendoza Zamora, Valentina; Montoya Rodríguez, Brayan; Shao, Wenxin.

Key word：Computer vision, Smart Bike Rack, Raspberry Pi, YOLO, Fast R-CNN, ARIMA, Random Forest, Telegram chatbot.

Full documentation and report: https://plum-tote-ee4.notion.site/Smart-Bike-Rack-Polito-675c49a4151c4cdd970232132840eb48
