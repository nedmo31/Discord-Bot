import urllib.request
import discord
import math

client = discord.Client()

apiKey = 'get your own' # I can't share mine :(

#Players in DotA 2 matches that can be bought and sold
class Player :
    def __init__(self, name, num, val) :
        self.name = name
        self.num = num
        self.val = val

class PlayerPointer :
    def __init__(self, player, boughtAt, quantity) :
        self.player = player
        self.boughtAt = boughtAt
        self.quantity = quantity

global playerList
playerList = {} # name ; Player
global userList
userList = {} # userID ; User
global lastMatchID
lastMatchID = 1 #used to make sure you cannot update past matches

#A User is anyone who makes an account to buy and sell Players
#Each Discord account can only make one
class User : 
    def __init__ (self, name, money, players, ID) :
        self.name = name
        self.money = money
        self.players = players
        self.ID = ID 

    #Adds up money and value of investments 
    def netWorth(self) :
        net = self.money
        for accountPlayer in self.players :
            net += accountPlayer.player.val * accountPlayer.quantity
        return round(net, 2)

    #Buys quantity of players if user has enough money,
    #Buys as many as possible if not
    def buyPlayer(self, playerName, quantity):
        if (playerName not in playerList or playerList[playerName].val == -1) :
            return 0 # Player doesn't exist    
        cost = playerList[playerName].val * quantity
        if self.money < cost : # Buys as many as possible if they can't afford entered quantity
            quantity = math.floor(self.money / playerList[playerName].val)
            cost = playerList[playerName].val * quantity
        for p in self.players :
            if p.player.name == playerName : # User already has a playerPointer for this player
                p.quantity += quantity
                self.money -= cost
                return quantity

        # If the function reaches this, it means they don't have the playerPointer yet
        self.players.append(PlayerPointer(playerList[playerName], playerList[playerName].val, quantity))
        self.money -= cost
        return quantity


    #Sells quantity of players if user has that many,
    #Sells as many as possible if not
    def sellPlayer(self, playerName, quantity):
        if (playerName not in playerList or playerList[playerName].val == -1) :
            return 0 # Player doesn't exist 
        for p in self.players :
            if p.player.name == playerName : # found player we're talking about
                if quantity > p.quantity :
                    quantity = p.quantity
                p.quantity -= quantity
                self.money += quantity * p.player.val
                if p.quantity == 0 :
                    self.players.remove(p)
                return quantity
        

    #returns a string representing the account
    def seeAccount(self) :
        output = 'Account Summary: \n'
        output += self.name + "  $" + str(round(self.money,2)) + '\n'
        for accountPlayer in self.players :
            output += str(accountPlayer.quantity) + 'x ' + accountPlayer.player.name + ' ~ $' + \
                str(accountPlayer.player.val) + '\t^' + str(round(accountPlayer.player.val-accountPlayer.boughtAt,2)) + '^\n'
        output += 'Net Worth: ' + str(self.netWorth())
        return output


#Returns a string representing the Players on the market
def seePlayerList() :
    output = 'Player List: \n'
    for player in playerList.values() :
        output += player.name + ' ~ $' + str(player.val) + '\n'
    return output

#Returns a string representing the Users 
def seeUserList() :
    output = 'Player\t\tNet Worth\n'
    for user in userList.values() :
        output += str(user.name) + '\t\t$' + str(user.netWorth()) + '\n'
    return output

#Save the users in a text file 
def saveUsers() :
    f = open('user_data.txt', 'w') 
    for user in userList.values() :
        f.write(str(user.ID)+' '+user.name+' '+str(user.netWorth())+'\n')
    f.close()

#Read the users from the text file and create user list from that
def readUsers() :
    f = open('user_data.txt', 'r')
    for line in f.readlines() :
        if len(line) <= 1 :
            continue
        line = line.split(' ')
        userList[line[0]] = User(line[1],float(line[2]),[],line[0])
    f.close()

#Save the players in a text file 
def savePlayers() :
    f = open('player_data.txt', 'w') 
    for player in playerList.values() :
        f.write(str(player.num)+' '+player.name+' '+str(player.val)+'\n')
    f.close()

#Read the players from the text file and create player list from that
def readPlayers() :
    f = open('player_data.txt', 'r')
    for line in f.readlines() :
        if len(line) <= 1 :
            continue
        line = line.split(' ')
        playerList[line[1]] = Player(line[1],line[0],float(line[2]))
    f.close()
        
# Takes a string and makes the first index of the string 
# 2 past the last part of the specified string
# Used to find "kills":3, and such in the API
def nextOcc(list, string, charsPast = 2) :
    try :
        list = list[list.find(string)+len(string)+charsPast:]
        return list
    except :
        print('something went wrong')
        return list

# Updates the list of current Players with the 
# match ID entered in. If none of the players 
# are in the game nothing happens. Also, the match
# has to be more recent than the last one entered
def updatePlayersWithMatch(ID) :
    #Get the match data from the API
    link = 'https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/V001/?match_id='+str(ID)+'&key='+apiKey
    website = urllib.request.urlopen(link)           
    contents = website.read().decode()
    
    i = 1 #To look at each of the ten players
    while(i < 11) :
        #Find the next player
        contents = nextOcc(contents, 'account_id')

        #Checks if the account_id matches any of the Players registered
        for player in playerList:
            if (playerList[player].num == contents[:contents.find(',')]) : #Player in data is a player we want
                print('found '+player)
                #   gets important info to calculate their value
                contents = nextOcc(contents, 'kills')
                kills = int(contents[:contents.find(',')])
                contents = nextOcc(contents, 'deaths')
                deaths = int(contents[:contents.find(',')])
                contents = nextOcc(contents, 'assists')
                assists = int(contents[:contents.find(',')])
                contents = nextOcc(contents, 'gold_per_min')
                gpm = int(contents[:contents.find(',')])
                contents = nextOcc(contents, 'xp_per_min')
                xpm = int(contents[:contents.find(',')])

                #Uses their KDA, gold and experience to determine their value for the match, and assigns the value
                change = ((kills+assists*1.3)/(deaths+4)) / 3.3 + ((gpm+xpm) / 3000) # a value roughly between .5 and 3
                playerList[player].val = round(playerList[player].val*change, 2)
                break
        i+=1
            
#The message thats displayed when user inputs $help
helpMessage = '$registerPlayer (userID) (name) <-- Add a player as a stonk\n'
helpMessage += '$me (name)<-- Prints out your data or registers your account. Put name if registering\n'
helpMessage += '$list <-- Lists all available players to purchase\n'
helpMessage += '$update (matchID) <-- updates players value based on match entered\n'
helpMessage += '$buy (playerName) (amount) <-- buys the amount specified of the player\n'
helpMessage += '$sell (playerName) (amount) <-- sells the amount specified of the player\n'
helpMessage += '$ranks <-- outputs list of users and their net worth'

# The bot responds asychronously to messages in the discord channel
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_disconnect():
    print('Disconnected')
    savePlayers()
    saveUsers()

@client.event
async def on_message(message):
    if message.author == client.user:
        return # Doesn't check messages from itself

    # Print help menu
    if message.content.startswith('$help'):   
        await message.channel.send(helpMessage)

    # Register a new Player 
    elif message.content.startswith('$registerPlayer'):
        IDandName = message.content[16:]
        userID = IDandName[:IDandName.find(' ')]
        name = IDandName[IDandName.find(' ')+1:]
        print(message.content.find(' ')+1)
        print(type(name),name)
        playerList[name] = Player(name, userID, 100)
        print(playerList[name].name)
        # await message.channel.send('added')

    # Print out user info or make an account
    elif message.content.startswith('$me'):
        userNum = str(message.author.id)
        if (userNum not in userList.keys()) : #Making a new account
            if (len(message.content) >= 4) :
                userList[userNum] = User(message.content[4:], 500, [], userNum)   
                print('new user registered')
            else :
                await message.channel.send('You need a name!')
        await message.channel.send(userList[userNum].seeAccount())

    # list the available players for buying/selling
    elif message.content == '$list' :
        await message.channel.send(seePlayerList())

    # Update the player values with a match ID
    elif message.content.startswith('$update'):
        global lastMatchID
        matchID = message.content[8:]
        print(matchID)
        if (int(matchID) > int(lastMatchID)) :
            lastMatchID = matchID
            updatePlayersWithMatch(matchID)
            await message.channel.send('Updated ')
            await message.channel.send(seePlayerList())
        else :
            await message.channel.send('Invalid MatchID')
        
    # Buy a player
    elif message.content.startswith('$buy') :
        info = message.content[5:]
        playerName = info[:info.find(' ')]
        try :
            amount = int(info[info.find(' ')+1:])
            bought = userList[str(message.author.id)].buyPlayer(playerName, amount)
            output = 'Bought '+str(bought)
            output += '. Balance: $' + str(round(userList[str(message.author.id)].money,2))
            await message.channel.send(output)
        except :
            await message.channel.send('$buy (player name) (amount)') 

            
    # Sell a player
    elif message.content.startswith('$sell') :
        info = message.content[6:]
        playerName = info[:info.find(' ')]
        try :
            amount = int(info[info.find(' ')+1:])
            bought = userList[str(message.author.id)].sellPlayer(playerName, amount)
            output = 'Sold '+str(bought)
            output += '. Balance: $' + str(userList[str(message.author.id)].money)
            await message.channel.send(output)
        except :
            await message.channel.send('$sell (player name) (amount)')

    # List the users and their net worth
    elif message.content == '$ranks' :
        await message.channel.send(seeUserList())


    #Hidden commands

    #Save
    elif message.content == '$save':
        savePlayers()
        saveUsers()
        await message.channel.send('Saved :)')

    #Removes a Player from the list
    elif message.content.startswith('$removePlayer') :
        name = message.content[14:]
        if name in playerList :
            playerList.pop(name)

    # Remove a user 
    elif message.content.startswith('$gameend') :
        name = message.content[9:]
        for person in userList.values() :
            if person.name == name :
                del userList[person.ID]
                break;

    # Give a user money
    elif message.content.startswith('$give') :
        info = message.content[6:]
        playerName = info[:info.find(' ')]
        if userList[str(message.author.id)].name == 'Nedmo' :
            amount = int(info[info.find(' ')+1:])
            for u in userList.values() :
                if u.name == playerName :
                    u.money += amount
        else :
            await message.channel.send('Good try')

# Read in saved data
readUsers()
readPlayers()

# Run the bot
client.run('') # <-- The bot's password goes there


