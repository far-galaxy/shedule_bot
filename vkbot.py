# -*- coding: utf-8 -*-
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard
from vk_api.utils import get_random_id
import os


class VKBot(object):
    def __init__(self, token, group_id, debug=True, admins=None, debug_msg = "Debug"):

        self.vk = vk_api.VkApi(token=token)
        self.longpoll = VkLongPoll(self.vk, wait=1)
        
        self.keyboard = VkKeyboard()
        self.inline = VkKeyboard(inline = True)

        self.debug = debug
        self.admins = admins
        if debug == True and self.admins == None:
            raise "Debug is enabled, but no admins"        
        self.group_id = group_id
        self.debug_msg = debug_msg
        
    def clear_keyboard(self):
        """Clears the object's keyboards"""
        self.keyboard = VkKeyboard()
        self.inline = VkKeyboard(inline = True)

    def check_file(file):
        """Checking and loading information from file.
        Useful for keeping tokens and other properties
        
        Args:
            file: path of file
            
        Returns:
            str: A content of file
        """   
        
        if len(file.split("/")) > 1:
            f = file.split("/")[-1]
            path = os.path.abspath(file.split("/")[-2])+f"/{f}.txt"
        else:
            path = f"{file}.txt"

        if os.path.exists(f"{path}"):
            info = open(f"{path}", "r", encoding="utf-8").read()
        else:
            info = input(f"{file} file not found. Please type {file} now:")
            file = open(f"{path}", "w")
            file.write(info)
            file.close()
        return info

    def get_messages(self):
        """Returns list of received messages"""
        events = self.longpoll.check()

        messages = []
        for event in events:
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and not event.from_chat:
                request = event.text
                uid = event.user_id
                debug = self.debug
                if (debug and uid not in self.admins):
                    self.send(uid, self.debug_msg)
                elif (debug and uid in self.admins) or not debug:
                    atts = self._parse_attachments(event.attachments)
                    messages.append({"uid": uid, "message": request, "attachments": atts})
            
            # Mark as read chat messages        
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.from_chat:
                self.mark_as_read(2000000000 + event.chat_id)

        return(messages)
    
    def _parse_attachments(self, attachments):
        """Converts JSON of attachments to list"""
        
        atts_list = []
        for i in range(1, len(attachments)//2+1):
            atts_list.append(attachments[f'attach{i}_type'] + attachments[f'attach{i}'])
        return atts_list

    def send(self, user_id, message, key=None, attachment=None):
        """Send message"""
        
        # replace wall link to wall attachment        
        wall = message.find("https://vk.com/")       
        if wall != -1:     
            attachment = message[message.find("vk.com/")+7:]
            message = message[:wall] 
        else:
            attachment = None
            
        msg = {}
        msg['user_id'] = user_id
        msg['random_id'] = get_random_id()
        msg['message'] = message
        if key != None:
            msg['keyboard'] = key
        if attachment != None:
            msg['attachment'] = attachment
        return self.vk.method('messages.send', msg)
    
    def typing(self, uid):
        """Make visiblity of typing text"""
        self.vk.method('messages.setActivity', {'user_id':uid, 'type':'typing', 'group_id': self.group_id}) 
        
    def mark_as_read(self, uid):
        """Mark last messages as read"""
        self.vk.method('messages.markAsRead', {'peer_id':uid, 'group_id': self.group_id})
        
    def mailing(self, ids, message):
        """Mailing messages for users in ID's list"""
            
        for i in ids:
            self.send(i, message)  
    
    def get_users(self):
        """Returns list of users, chatting with bot
        
        Returns:
            list: ID's of users, chatting with bot
        
        """
        
        info_chat = self.vk.method('messages.getConversations', {'group_id': str(self.group_id)})['items']
        chats = [i['conversation']['peer']['id'] for i in info_chat]
        
        # Delete group chats
        for user in chats:
            if len(str(user)) == 10 and str(user)[0] == "2":
                chats.remove(user)
                
        return chats
    
class VKStatus():
    def __init__(self, token, group_id):

        self.vk = vk_api.VkApi(token=token)
        self.group_id = group_id
        
    def status(self, text):
        responce = self.vk.method("status.set", {"text": text, "group_id" : self.group_id})     
        return responce

# Test programm: echo
if __name__ == "__main__":

    token = VKBot.check_file("settings/token")
    group_id = VKBot.check_file("settings/group_id")
    bot = VKBot(token, group_id, debug=False)
    
    print(bot.get_users())

    while True:
        msg = bot.get_messages()
        if msg != []:
            print(msg)
            txt = msg[0]["message"].split("~")
            if txt[0] == "add":
                print(msg[0]["attachments"])
