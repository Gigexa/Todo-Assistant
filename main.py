import customtkinter as ctk
from tkinter import messagebox
import requests
import threading
import json
import ast
import sqlite3

root = ctk.CTk()
root.title("Todo Assistant")

x = root.winfo_screenwidth()//2 - (800//2)
y = root.winfo_screenheight()//2 - (500//2)
root.geometry(f"900x600+{x}+{y}")
root.resizable(False,False)


def send_text(text=None):
	text = entry.get()
	entry.delete(0, 'end')
	ai_label.configure(text="Thinking... ")
	button.configure(state='disabled')


	threading.Thread(
		target = submit,
		args = (text,),
		daemon = True
	).start()


def submit(text=None):

	prompt = f"""
				----------------------------
				You are a AI Todo Assistant. 
				Your tools:
				1. add_todo
				2. delete_todo
				3. edit_todo
				You should decide what tool to use according to user's prompt.

				if there is 'add' in user's prompt, you respose should be:
				{{'tool': 'add_todo', 'text':whatever User Wants In here, 'date':User's indicated date example: today}}
				if there is 'delete' in user's prompt, your response should be:
				{{'tool':'delete_todo', 'text':Whatever user wants to delete}}
				if there is 'update' or 'edit' in user's prompt, your response should be:
				{{'tool':'edit_todo', 'old_text':whatever user wants to edit, 'new_text': new text that user gives you}}
				
				if the prompt is regular, not asking you to use tools, respond as you like. not with json, but normally.
				User's prompt: {text}
	        """
	response = requests.post(
		"http://localhost:11434/api/generate",
		 json = {
		 'model':'mistral',
		 'prompt': prompt,
		 'stream': False

		}
	)

	text = response.json()['response']
	root.after(0,get_proper_tool, text)


class Manager:
	def __init__(self):
		self.database = Database()

	def get_data_from_db(self):
		return self.database.get_data()


	def delete_data_from_db(self,text,everything = False):
		text = text.split(" date:")
		text = text[0]
		text = text.lower()
		self.database.delete_data(text)


	def add_data_to_db(self,text,date):
		text = text.lower()
		self.database.insert_data(text,date)

	def edit_data_in_db(self,old_text,new_text):
		new_text = new_text.split(" date:")[0]
		self.database.edit_data(old_text,new_text)
		new_text = new_text.lower()

class Todo:
	def __init__(self):
		self.TOOLS = {"add_todo":self.add_todo,
			"delete_todo": self.delete_todo,
			"edit_todo": self.edit_todo}
		self.todo_list = []
		self.count = 0
		self.radio_buttons = []
		self.add_buttons()
		self.manager = Manager()
		self.check_todos(refresh=True)
		



	def check_todos(self,refresh = False):
		data = self.manager.get_data_from_db()

		for i in data:
			self.add_todo(i[0],i[1],refresh)


	def add_buttons(self):
		self.frame_for_text = ctk.CTkScrollableFrame(frame_main, width = 600, height=500, border_width = 1)
		self.frame_for_text.pack(side = "top")
		self.frame_for_buttons = ctk.CTkFrame(frame_main, width = 600, height = 100)
		self.frame_for_buttons.pack(side = "bottom")

		self.add = ctk.CTkButton(self.frame_for_buttons, text ="Add",command = self.add_manually)
		self.add.grid(column=0,row=0,pady = 5)
		self.remove = ctk.CTkButton(self.frame_for_buttons, text = "Remove", command = self.remove_manually)
		self.remove.grid(column = 1, row= 0, pady =5,padx=5)


	def remove_manually(self):
		self.add.grid_forget()
		self.remove.grid_forget()
		for i in range(len(self.todo_list)):
			rb_status = ctk.StringVar()
			radiobutton = ctk.CTkRadioButton(self.frame_for_text, text = "",variable = rb_status, value= "True")
			radiobutton.grid(column=1,row = i,padx = 10)
			self.radio_buttons.append((radiobutton,rb_status))

		self.ok = ctk.CTkButton(self.frame_for_buttons, text = "Ok", command = self.confirm_rm)
		self.ok.grid(column=0,row=0,pady=5)
		self.cancel = ctk.CTkButton(self.frame_for_buttons, text = "Cancel", command = self.cancel_rm)
		self.cancel.grid(column = 1, row=0, pady =5)

	def confirm_rm(self):
		to_pop = None
		for i in range(len(self.radio_buttons)):
			if self.radio_buttons[i][1].get() == "True":
				#print(len(self.todo_list))
				self.todo_list[i].grid_forget()
				self.todo_list[i].destroy()
				self.manager.delete_data_from_db(self.todo_list[i].cget("text"))
				self.radio_buttons[i][0].grid_forget()
				self.radio_buttons[i][0].destroy()
				self.count -= 1
				to_pop = i
			else:
				continue

		self.todo_list.pop(to_pop)
		self.radio_buttons.pop(to_pop)
		self.ok.destroy()
		self.cancel.destroy()
		self.add.grid(column = 0, row =0, pady =5)
		self.remove.grid(column = 1, row =0, pady=5, padx=5)
		self.refresh()


	def refresh(self):
		for widget in self.frame_for_text.winfo_children():
			widget.destroy()
		self.count = 0
		self.todo_list = []
		self.radio_buttons =[]
		self.check_todos(refresh=True)


	def cancel_rm(self):

		for i in self.radio_buttons:
			try:
				i[0].destroy()
			except:
				continue

		self.ok.destroy()
		self.cancel.destroy()
		self.add.grid(column = 0, row =0, pady =5)
		self.remove.grid(column = 1, row =0, pady=5, padx=5)


	def add_manually(self):
		self.remove.grid_forget()
		self.add.grid_forget()
		self.entry_for_todo = ctk.CTkEntry(self.frame_for_buttons, width = 200, height = 50)
		self.entry_for_todo.grid(column=0,row = 1,pady=5)
		self.ok = ctk.CTkButton(self.frame_for_buttons, text = "Ok", command = self.confirm_add)
		self.ok.grid(column = 1, row = 1)
		self.cancel = ctk.CTkButton(self.frame_for_buttons, text = "Cancel", command = self.cancel_add)
		self.cancel.grid(column = 1, row = 2)

	def cancel_add(self):
		self.entry_for_todo.destroy()
		self.ok.destroy()
		self.cancel.destroy()
		self.add.grid(column = 0, row=0,pady=5)
		self.remove.grid(column=1, row=0, pady=5,padx=5)

	def confirm_add(self):
		text = self.entry_for_todo.get()
		text = text.lower()
		if " date:" in text:
			self.entry_for_todo.destroy()
			self.ok.destroy()
			self.cancel.destroy()
			todo_text = ctk.CTkLabel(self.frame_for_text, text = f'{text}')
			self.todo_list.append(todo_text)
			todo_text.grid(column=0,row=f"{self.count}")
			self.count+=1
			self.manager.add_data_to_db(text.split(" date:")[0],text.split(" date:")[1])
			self.add.grid(column= 0, row= 0, pady=5)
			self.remove.grid(column = 1, row = 0, pady = 5,padx=5)
		else:
			messagebox.showinfo(title='Error',message = "Please enter todo in this format: Todo date: today")

	def add_todo(self,text,date,refresh = False):
		text = text.lower()
		if refresh:
			todo_text = ctk.CTkLabel(self.frame_for_text, text = f"{text} date: {date}")
			self.todo_list.append(todo_text)
			todo_text.grid(column = 0, row = f'{self.count}')
			#self.manager.add_data_to_db(text,date)
			self.count+=1
		else:
			todo_text = ctk.CTkLabel(self.frame_for_text, text = f"{text} date: {date}")
			self.todo_list.append(todo_text)
			todo_text.grid(column = 0, row = f'{self.count}')
			self.manager.add_data_to_db(text,date)
			self.count+=1




	def delete_todo(self,text,date):
		text = text.lower()
		for index,i in enumerate(self.todo_list):
			if text in i.cget("text"):
				i.grid_forget()
				i.destroy()
				self.manager.delete_data_from_db(i.cget("text"))
				self.todo_list.pop(index)
				self.count-=1
			else:
				continue

	def edit_todo(self,old_text,new_text):
		old_text = old_text.lower()
		new_text = new_text.lower()
		
		for i in self.todo_list:
			
			if old_text in i.cget("text"):
				new_text = new_text +" "+ i.cget("text").lstrip(old_text)
				self.manager.edit_data_in_db(old_text,new_text)
				# print(old_text)
				# print(new_text)
				self.refresh()
			else:
				continue





class Database:
	def __init__(self):
		self.connection = sqlite3.connect("TestDB.db")
		self.cursor = self.connection.cursor()
		self.cursor.execute("CREATE TABLE IF NOT EXISTS Todos(text,date)")

	def get_data(self):
		comm = self.cursor.execute("SELECT * FROM Todos")
		data = comm.fetchall()

		return data

		

	def insert_data(self,text,date):
		comm = self.cursor.execute(f"""INSERT INTO Todos VALUES
										('{text}','{date}')""")
		self.connection.commit()
	def delete_data(self,text, everything = False):
		if everything:
			self.cursor.execute("DELETE FROM Todos")
			self.connection.commit()
		else:
			#print(text)
			self.cursor.execute(f"DELETE FROM Todos WHERE text='{text}'")
			self.connection.commit()

	def edit_data(self,old_text,new_text):
		self.cursor.execute(f"SELECT date FROM Todos WHERE text = '{old_text}'")
		date = self.cursor.fetchall()
		date = date[0][0]
		self.cursor.execute(f"DELETE FROM Todos WHERE text = '{old_text}'")
		# print(old_text)
		# print(new_text)
		self.connection.commit()
		self.cursor.execute(f"""INSERT INTO Todos VALUES 
								('{new_text}',"{date}")""")
		self.connection.commit()
		




def get_proper_tool(response):
	
	#response = json.loads(response)
	try:
		response = ast.literal_eval(response)

		if response['tool'] == "edit_todo":
			tool = response['tool']
			old_text = response['old_text']
			new_text = response['new_text']
			#print(response)
			todo.TOOLS[tool](old_text,new_text)
			update_ui("Success")
		else:
			try:
				text = response['text']
				tool = response['tool']
				date = response['date']
				todo.TOOLS[tool](text,date)
				update_ui("Success")
			except KeyError:
				try:
					text = response['text']
					tool = response['tool']
					date = "today"
					todo.TOOLS[tool](text,date)
					update_ui("Success")
				except KeyError:
					update_ui("Sorry Couldn't help you with that, my bad.")
	except KeyError,SyntaxError:
		update_ui(response)


def update_ui(response):
	ai_label.configure(text = response)
	button.configure(state = 'normal')



frame_main = ctk.CTkFrame(root,width = 600,height = 600,border_width = 0)
frame_main.pack(side="left", fill = "both", expand = True)
frame_main.pack_propagate(False)
frame_ai = ctk.CTkFrame(root,width = 300, height = 600, border_width =5)
frame_ai.pack(side='right')

chat_label_frame = ctk.CTkScrollableFrame(frame_ai,width =300, height = 500)
chat_label_frame.pack(fill='both', expand=True)
chat_label_frame.pack_propagate(False)

buttons_entry_frame = ctk.CTkFrame(frame_ai, width =300, height = 100)
buttons_entry_frame.pack(fill='both',expand = True)
buttons_entry_frame.pack_propagate(False)


ai_label = ctk.CTkLabel(chat_label_frame, text = """Welcome to Todo Assistant, I am an AI which can help you with daily tasks.\n\nI have few tools which I can use:\n\nI can create a Todo for you;\n\nI can delete one or edit one for you;\n\nAlso you can ask questions about them and I will be ready to asnwer;
														""", font = ("Arial", 12, "bold"), wraplength = 200)
ai_label.grid(column=0,row=0,sticky = 'W')

entry = ctk.CTkEntry(buttons_entry_frame, width= 200,height =80)
entry.grid(column=0,row=0,pady=5)
entry.bind("<Return>",send_text)
button = ctk.CTkButton(buttons_entry_frame, text = "send", width =20,command = send_text)
button.grid(column=1,row=0,padx=5)
todo = Todo()
root.mainloop()