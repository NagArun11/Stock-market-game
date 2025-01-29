import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from game.gamestate import Gamestate
from django.http import HttpResponse

userDict={}
gameDict={}

class UserAlreadyExistsError(Exception):
    pass

class RoomNotFoundError(Exception):
    pass

class RoomLimitExceededError(Exception):
    pass

class GameAlreadyStartedError(Exception):
    pass

class ChatConsumer(WebsocketConsumer):
    
    def stringToBool(self,string):
        if string=="True":
            return True 
        else: 
            return False

    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.queryString=self.scope["query_string"].decode("utf-8")
        self.create, self.join, self.username = self.queryString.split('&')
        self.create = self.stringToBool(self.create[7:])
        self.join = self.stringToBool(self.join[5:])
        self.username = self.username[9:]
        flag=0
        if self.create:
            if self.room_name in userDict:
                self.accept()
                self.send(json.dumps({"type":"ErrorMessage","data":{"errorCode":700,"message":"Room with this id is already created"}}))
                self.close(code=3000)
                return
            userList=[self.username]
            userDict[self.room_name]=userList
        else:
            if self.room_name in userDict:
                userList=userDict[self.room_name]
                if self.username not in userList:
                    if self.room_name in gameDict:
                        for i in gameDict[self.room_name].userState:
                            if gameDict[self.room_name].userState[i]["username"]==self.username:
                                userList.insert(i,self.username)
                                userDict[self.room_name]=userList
                                flag=1
                                break
                        if flag==0:
                            self.accept()
                            self.send(json.dumps({"type":"ErrorMessage","data":{"errorCode":702,"message":"Game has already started"}}))
                            self.close(code=3000)
                            return
                    else:
                        userList.append(self.username)
                        userDict[self.room_name]=userList
                else: 
                    self.accept()
                    self.send(json.dumps({"type":"ErrorMessage","data":{"errorCode":701,"message":"User with same username already present in this room"}}))
                    self.close(code=3000)
                    return
            else:
                self.accept()
                self.send(json.dumps({"type":"ErrorMessage","data":{"errorCode":704,"message":"Room trying to join does not exist"}}))
                self.close(code=3000)
                return
                
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_name, self.channel_name
        )
        self.accept()
        async_to_sync(self.channel_layer.group_send)(
            self.room_name, {"type": "getRoomDetails", "data": {"room_name":self.room_name,"userArr":userDict[self.room_name],"room_status":True}}
        )
        if flag==1:
            self.rejoin()
            


    def disconnect(self,close_code=1000):
        if close_code==3000:
            async_to_sync(self.channel_layer.group_discard)(
                self.room_name, self.channel_name
            )
        else:
            if self.room_name in userDict:
                if self.username in userDict[self.room_name]:
                    userDict[self.room_name].remove(self.username)
                    if self.room_name in gameDict:
                        result=gameDict[self.room_name].checkIsAdmin(self.username,userDict[self.room_name])
                    if self.room_name in gameDict:
                        if result:
                            async_to_sync(self.channel_layer.group_send)(
                            self.room_name, {"type": "adminChanged", "data":gameDict[self.room_name]}
                            )
                    async_to_sync(self.channel_layer.group_send)(
                    self.room_name, {"type": "getRoomDetails", "data":{"message":"Someone Left","userArr":userDict[self.room_name]}}
                    )
                    if len(userDict[self.room_name])==0:
                        userDict.pop(self.room_name)
                        if self.room_name in gameDict:
                            gameDict.pop(self.room_name)
                    async_to_sync(self.channel_layer.group_discard)(
                    self.room_name, self.channel_name
                    )                  
    # Called when message is received from frontend
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["data"]
        type=text_data_json["type"]
        if type=="onStartGame":
            if userDict[self.room_name][0]==self.username:
                if "configs" in message:
                    gameState=Gamestate(userDict[self.room_name],message["totalMegaRounds"],message["configs"])
                else:
                    gameState=Gamestate(userDict[self.room_name],message["totalMegaRounds"])
                gameState.startMegaRound()
                gameDict[self.room_name]=gameState
                async_to_sync(self.channel_layer.group_send)(
                self.room_name, {"type": "onStartGame", "data":{"userArr":userDict[self.room_name],"totalMegaRounds":message["totalMegaRounds"]}}
                )
            else:
                raise Exception("User not authorized to start the game")
        elif type=="buy":
            gameDict[self.room_name].buy(message["userId"],message["companyId"],message["numberOfStocks"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif type=="sell":
            gameDict[self.room_name].sell(message["userId"],message["companyId"],message["numberOfStocks"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )        
        elif type=="pass":
            if gameDict[self.room_name].playerOrder[gameDict[self.room_name].currentTurn]==message["userId"]:
                gameDict[self.room_name].passTransaction(message["userId"])
                async_to_sync(self.channel_layer.group_send)(
                    self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
                )
        elif type=="crystal":
            gameDict[self.room_name].crystal(message["userId"],message["crystalType"],message["companyId"],message["numberOfStocks"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif type=="circuit":
            gameDict[self.room_name].circuit(message["companyId"],message["circuitType"],message["denomination"])
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif type=="startMegaRound":
            gameDict[self.room_name].startMegaRound()
            gameDict[self.room_name].netChangeInCompanyByUsers={}
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"transaction","data":gameDict[self.room_name]}
            )
        elif type=="getRoomDetails":
            async_to_sync(self.channel_layer.group_send)(
                self.room_name, {"type":"getRoomDetails","data":message}
            )
        elif type=="endMegaRound":
            netChange=gameDict[self.room_name].netChangeInCompanyByUsers
            priceBook=gameDict[self.room_name].priceBook
            response={"type":"endMegaRound","data":{"netChange":netChange,"priceBook":priceBook}}
            self.send(json.dumps(response))
        elif type=="endGame":
            response=gameDict[self.room_name].endGame()
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"endGame","data":{"results":response}}
            )
            gameDict.pop(self.room_name)
        elif type=="emoticon":
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"emoticon","data":{"emoji":message,"username":self.username}}
            )
        elif type=="kickUser":
            user=gameDict[self.room_name].kickUser(message)
            async_to_sync(self.channel_layer.group_send)(
                self.room_name,{"type":"kickUser","data":{"username":user["username"],"gameState":gameDict[self.room_name]}}
            )

    def kickUser(self,event):
        print(event)
        gameState=event["data"]["gameState"].toJSON()
        event["data"]["gameState"]=json.loads(gameState)
        self.send(text_data=json.dumps(event))
        # response={"type":"kickUser"}
        # response["data"]["username"]=event["username"]
        # gameState=event["gameState"]



    def emoticon(self,event):
        self.send(text_data=json.dumps(event))

    def onStartGame(self,event):
        response={"type":"onStartGame"}
        gameState=gameDict[self.room_name]
        event=gameState.toJSON()
        event=json.loads(event)
        response["data"]=event
        self.send(text_data=json.dumps(response))

    def transaction(self,event):
        response={"type":"roundInfo"}
        event=event["data"].toJSON()
        event=json.loads(event)
        response["data"]=event
        self.send(text_data=json.dumps(response))

    def endGame(self,event):
        self.send(text_data=json.dumps(event))
    # Called when group_send is called or message is sent to frontend
    def getRoomDetails(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))
    def rejoin(self):
        response={"type":"RejoinMessage"}
        gameState=gameDict[self.room_name].toJSON()
        gameState=json.loads(gameState)
        response["data"]=gameState
        self.send(text_data=json.dumps(response))

    def adminChanged(self,event):
        response={"type":"adminChanged"}
        event=event["data"].toJSON()
        event=json.loads(event)
        response["data"]=event
        self.send(text_data=json.dumps(response))

