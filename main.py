#Import everything
import os
from discord.ext import commands
from keep_alive import keep_alive
from replit import db
from datetime import datetime, date, timedelta
import math
import gspread
import json
import ast

#Connecting to Google Sheets API
mystring = os.environ['json']
my_dict = ast.literal_eval(mystring)
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(my_dict, f, sort_keys = True, ensure_ascii=False, indent=4)
sa = gspread.service_account(filename = 'data.json')
sh = sa.open("Stat_Sheets")
wks = sh.worksheet("Data")
os.remove('data.json')

#Returns date in correct format for Google Sheets
def changedate(day = date.today()):
  day =str(day)
  return '=DATE(' + day.replace("-",",") + ')'

#Creates spreadsheet template
if wks.acell('A1').value == None:
  wks.update('A1:M1', [["Date","Sport_bool","Sport_t_xp","Sport_const","Japanese_bool","Japanese_t_xp","Japanese_const","Analytics_bool","Analytics_t_xp","Analytics_const","Mental_bool","Mental_t_xp","Mental_const"]])
  wks.update('A2', changedate(), raw = False)
  wks.update('D2:D5', [[0],[0],[changedate()],[changedate()]], raw = False)
  wks.update('G2:G5', [[0],[0],[changedate()],[changedate()]], raw = False)
  wks.update('J2:J5', [[0],[0],[changedate()],[changedate()]], raw = False)
  wks.update('M2:M5', [[0],[0],[changedate()],[changedate()]], raw = False)

#Date when the bot first started
firstdate = datetime.strptime(wks.acell('A2').value, '%d/%m/%Y').date()

#Global variable which is needed for leveling up. Each level is twice the basexplimit
basexplimit = 1000

#Obtains the needed cell number
def getcell():
  return int(str(date.today()+timedelta(days=2)-firstdate).split()[0])

#Bot uses "$" sign for commands
client = commands.Bot(command_prefix = '$')

#Blueprint for all skills
class Skill:
  def __init__(self,name,code,xp,lvl, days, dayl):
    self.name = name
    self.code = code
    self.xp = xp
    self.lvl = lvl
    self.days = days
    self.dayl = dayl
  #Whenever a task is completed
  def complete(self):
    global basexplimit, boolcodes
    #Sets the date if null
    if wks.acell(f'A{getcell()}').value == None:
      wks.update(f'A{getcell()}',changedate(), raw = False)
    #Value must not be inserted yet
    if wks.acell(f'{self.code[0]}{getcell()}').value == None:
      #Checks for unrecorded data and sets fails
      if wks.acell(f'{self.code[0]}{getcell()-1}').value == None:
        for c in range(getcell()-1):
          if wks.acell(f'{self.code[0]}{c+1}').value == None:
            wks.update(f'A{c+1}',f'{changedate()}-{getcell()-c-1}', raw = False)
            wks.update(f'{self.code[0]}{c+1}', 'Failed')
            if self.lvl==1:
              wks.update(f'{self.code[1]}{c+1}',self.xp, raw = False)
            else:
              wks.update(f'{self.code[1]}{c+1}',f'{self.xp+2**(self.lvl-2)*basexplimit}', raw = False)
      reply = ""
      try:
        #Deducts xp if overdue
        if int(str(date.today()-self.dayl).split()[0]) > 2:
          self.xp-=10*self.lvl*int(str(date.today()-self.dayl).split()[0])
          reply = f"Congratulations on completing {self.name} excercise! Unfortunately, I have to deduct "+ str(10*self.lvl*int(str(date.today()-self.dayl).split()[0])-10) + f" {self.name} xp, because there were no logs for {str(date.today()-self.dayl).split()[0]} days, but don't give up! It's time to make a comeback!"
          self.xp+=10
          self.days = date.today()
        else:
        #Checks if there's a streak and grants bonus xp
          if int(str(date.today()-self.days).split()[0]) > 3 and int(str(date.today()-self.days).split()[0]) < 20:
            self.xp += 1*int(str(date.today()-self.days).split()[0])+10
            reply = "You're on " + str(date.today()-self.days).split()[0] + " days streak! Keep it up! You have gained " + str(1*int(str(date.today()-self.days).split()[0])+10) + f" {self.name} xp!"
          #Checks if the limit has been hit
          elif int(str(date.today()-self.days).split()[0]) >= 20:
            self.xp += 30
            reply = "You're on " + str(date.today()-self.days).split()[0] + f" days streak! Keep it up! You have gained 30 {self.name} xp (limit)!"
          #If there is no streak
          elif int(str(date.today()-self.days).split()[0]) >= 1:
              self.xp+=10
              reply = f"Well done! You have gained 10 {self.name} xp!"
      #If the difference between dates is less than 1. It is possible when the bot is first created
      except:
        self.xp+=10
        reply = f"Well done! You have gained 10 {self.name} xp!"
      self.dayl = date.today()
      #Checks for level ups level downs
      if self.xp>=2**(self.lvl-1)*basexplimit:
        self.xp-=2**(self.lvl-1)*basexplimit
        self.lvl+=1
      elif self.xp<0:
        if self.lvl !=1:
          self.lvl-=1
          self.xp+=2**(self.lvl-1)*basexplimit
        else:
          self.xp = 0
      #Updates every stat in the spreadsheet
      wks.update(f'{self.code[0]}{getcell()}','Completed')
      wks.update(f'{self.code[2]}2',self.xp)
      wks.update(f'{self.code[2]}4',changedate(self.days), raw = False)
      wks.update(f'{self.code[2]}5',changedate(self.dayl), raw = False)
      if self.lvl == 1:
        wks.update(f'{self.code[1]}{getcell()}',self.xp)
      else: 
        wks.update(f'{self.code[1]}{getcell()}',self.xp+2**(self.lvl-2)*basexplimit)
      wks.update(f'{self.code[2]}3',self.lvl)
    else:
      return f"You have already completed this today. Come back tomorrow!"
    
    return reply
  #Shows stats
  def stat(self):
    return f'**{self.name}** - Level {self.lvl} [{self.xp}/{2**(self.lvl-1)*basexplimit}] ({math.floor(self.xp/(2**(self.lvl-1)*basexplimit)*100)}%)\n'

#Class creation
csport = Skill("Sport", ['B','C','D'], int(wks.acell('D2').value), int(wks.acell('D3').value), datetime.strptime(wks.acell('D4').value, '%d/%m/%Y').date(), datetime.strptime(wks.acell('D5').value, '%d/%m/%Y').date())
cjapanese = Skill("Japanese", ['E','F','G'], int(wks.acell('G2').value), int(wks.acell('G3').value), datetime.strptime(wks.acell('G4').value, '%d/%m/%Y').date(), datetime.strptime(wks.acell('G5').value, '%d/%m/%Y').date())
canalytics = Skill("Analytics", ['H','I','J'], int(wks.acell('J2').value), int(wks.acell('J3').value), datetime.strptime(wks.acell('J4').value, '%d/%m/%Y').date(), datetime.strptime(wks.acell('J5').value, '%d/%m/%Y').date())
cmental = Skill("Mental", ['K','L','M'], int(wks.acell('M2').value), int(wks.acell('M3').value), datetime.strptime(wks.acell('M4').value, '%d/%m/%Y').date(), datetime.strptime(wks.acell('M5').value, '%d/%m/%Y').date())

#When bot starts
@client.event
#when the bot starts
async def on_ready():
  print('Stat Bot is ready!')

#Shows stats
@client.command(pass_context = True)
async def stats(ctx):
  await ctx.send(csport.stat()+cjapanese.stat()+canalytics.stat()+cmental.stat())
  await ctx.send("You're doing great! Keep ut up!")

@client.command(pass_context = True)
async def sport(ctx):
  await ctx.send(csport.complete())

@client.command(pass_context = True)
async def japanese(ctx):
  await ctx.send(cjapanese.complete())

@client.command(pass_context = True)
async def analytics(ctx):
  await ctx.send(canalytics.complete())

@client.command(pass_context = True)
async def mental(ctx):
  await ctx.send(cmental.complete())

@client.command(pass_context = True)
async def greeting(ctx):
  await ctx.send("Hi! I am a Stat Bot! I will make sure to help you achieve progress in your desired skills!\nIf you would like to view or change the code to personalise me, please use this link: https://github.com/KirillBungou/Stat-Bot")

#The bot is running on replit server. This command keeps replit from shutting down the bot
keep_alive()

#Starts the bot
client.run(os.environ['Token'])