from OthelloAi import SimpleAi
from Pieces import Tile, Wall
import os
import copy
import time

def Menu():
    menuRunning = True
    while menuRunning:
        game = Game() # Creates the object of game in the Game() class
        while True:
            print("\n[1] New Game\n[2] Load Game\n[3] Exit Program")
            try:
                option = int(input("\nEnter your option: "))
                if option > 0 and option < 4:
                    break
                if option < 1 or option > 3: 
                    print("\nPlease enter 1, 2, or 3.")
            except ValueError:
                print("\nPlease enter a number.")
        if option == 1: # Run a new game
            game.NewGame()
        elif option == 2: # Displays the saved games
            game.LoadGame()
        elif option == 3: # Exit program
            exit()

class Game(): # Contains all game logic methods
    
    symbols = ["●", "○"] # Variables used across the game, hence not "self.symbols"

    toCopy = ["board", "movesToGetThere", "symbols"] # Variables that need to be copied when making a new game

    def __init__(self):
        self.board = Board() # Upon instantiation, board is made into an object of the Board class, so it can use methods from Board()
        self.turn = "Player"
        self.state = "Running"

    def copy(self): # Custom copy method
        game = Game()
        game.__dict__ = {}
        for attr in self.__dict__:
            if attr in Game.toCopy:
                game.__dict__[attr] = copy.deepcopy(self.__dict__[attr])
            elif attr == "children":
                game.__dict__[attr] = []
            elif attr == "score":
                game.__dict__[attr] = 0
            elif attr == "gotoChild":
                game.__dict__[attr] = None
            else:
                game.__dict__[attr] = self.__dict__[attr]
            
        return game

    def NewGame(self, generateBoard=True): # Generate board is there so that the board won't be reset when loading a game
        self.StartGame(generateBoard)
        while self.state != "Finished":
            if self.turn == "Player":
                self.MakeUserMove()
            else:
                starttime = time.time()
                bestMove, optimalScore = SimpleAi(self.symbols[1], self, 3).RunMiniMax()
                self.MakeMove(self.symbols[1], bestMove.GetCoords(), bestMove)
                print("\nAi took %s seconds" % (time.time() - starttime).__round__(2)+" and played move: ["+str(bestMove)+"] with optimal advantage score ["+str(optimalScore)+"]")
                self.board.PrintBoard()
            self.SwitchTurns()

            if self.IsGameOver():
                self.state = "Finished"
                print("\nGame Over")
                score = self.board.CountDisks()
                print("\nPlayer:",score[0]," | Ai:",score[1])
                if score[0] > score[1]:
                    print("\nPlayer wins!")
                elif score[1] > score[0]:
                    print("\nAi wins!")
                else:
                    print("\nThe game ended in a tie.")

                # Gives the option to save the game
                self.SaveGame(score, self.state) # Score passed in as a variable so the game can be continued

                Menu()

    def SaveGame(self, score, state):
        nameOfGame = input("\nName this game: ")
        saveGame = open(state+"-"+nameOfGame+".txt", "w", encoding="utf-8") # Gives the game state, name, and encoding style

        # Records information to save as an array
        gameBoard = self.board.BoardToArray()

        # Write it to the file and close
        saveGame.write(str(gameBoard))
        saveGame.write("\nPlayer: "+str(score[0])+" | Ai: "+str(score[1])) # Adds the score of the game
        saveGame.close()

    def LoadGame(self):
        # Finds all files in the directory ending in .txt
        savedGames = [f for f in os.listdir('.') if f.endswith('.txt')]

        if len(savedGames) == 0:
            print("\nNo saved games found.")
            return
        
        # Displays all the saved games
        print("\nSaved games:")
        for i, filename in enumerate(savedGames):
            print(f"[{i+1}] {filename}")
        choice = input("\nEnter the number of the saved game you want to load (or 0 to cancel): ")
        
        try:
            choice = int(choice)
        except ValueError:
            print("\nInvalid input.")
            return
        
        if choice == 0:
            return

        if choice < 1 or choice > len(savedGames):
            print("\nInvalid choice.")
            return
        
        # Load the contents of the selected saved game file and display them
        with open(savedGames[choice-1], 'r', encoding="utf-8") as f:    
            contents = f.readlines() # Reads all the lines separately to help display the score later

            # If the chosen game is finished then it will only print the score and the board
            if savedGames[choice-1].startswith('Finished'):
                print("\nThis game is finished | "+contents[1])
                self.board.BoardFromArray(contents[0])
                self.board.PrintBoard()
                exit()
            # Otherwise, the game plays on
            else:
                self.board.BoardFromArray(contents[0])
                self.NewGame(False) # Do not reset the board

    def StartGame(self,generateBoard): # Runs methods to set the board up
        if generateBoard: # Due to loading up games that are part-way through
            self.board.GenerateBlankGrid()
            self.board.GenerateWalls()
            self.board.GenerateStartBoard()
        self.board.PrintBoard()

    def IsMoveValid(self, coords, symbol): # Checks to see if a specific move is valid, returns T/F
        toFlip = [] # List of tiles to be flipped
        validToFlip, toFlip = self.CreateLine(coords, symbol) # ValidToFlip is True if self.CreateLine() is True, toFlip is True if it has any values in it
        if self.DoCoordsExist(coords) and self.IsTileEmpty(coords) and self.IsNextToOpponent(coords, symbol) and validToFlip:
            return True, toFlip # If all are True, it returns True and toFlip
        else:
            return False, None # Otherwise it will return False and no other tiles will be flipped

    def FindValidMoves(self, symbol): # Finds a list of all valid moves
        validMoves = [] # List of valid moves
        for y in range(1, 9): # Iterates through all tiles in the board
            for x in range(1, 9):
                moveIsValid, toFlip = self.IsMoveValid([x,y],symbol) 
                # If move is valid then:
                # x and y value is added,
                # along with the tiles which are to be flipped
                if moveIsValid:
                    moveInfo = Move(x,y,toFlip)
                    validMoves.append(moveInfo)
        return validMoves
        
    def DoCoordsExist(self, coords): # Check if the coords exist
        if coords[0] <= 8 and coords[0] >= 1 and coords[1] <= 8 and coords[1] >= 1:
            return True # Location exists
        else:
            # print("\nTile does not exist")
            return False
    
    def IsTileEmpty(self, coords):
        if self.board.grid[coords[1]][coords[0]].symbol == " ":
            return True # Tile is empty
        else:
            # print("\nTile contains a disk")
            return False

    def IsNextToOpponent(self, coords, symbol):
        adjacentTiles = [
                         self.board.grid[coords[1] + 1][coords[0]].symbol,     # Down
                         self.board.grid[coords[1] - 1][coords[0]].symbol,     # Up
                         self.board.grid[coords[1]][coords[0] - 1].symbol,     # Left
                         self.board.grid[coords[1]][coords[0] + 1].symbol,     # Right
                         self.board.grid[coords[1] + 1][coords[0] + 1].symbol, # Up Left
                         self.board.grid[coords[1] + 1][coords[0] - 1].symbol, # Up Right
                         self.board.grid[coords[1] - 1][coords[0] + 1].symbol, # Down Left
                         self.board.grid[coords[1] - 1][coords[0] - 1].symbol  # Down Right
                        ]
        oppSymbol = self.symbols[1 - self.symbols.index(symbol)]
        if oppSymbol in adjacentTiles:
            return True
        else:
            # print("\nNot next to an opponent's tile")
            return False

    def CreateLine(self, coords, symbol): 
        # Checks to see if a line can be created,
        # Lists the tiles to be flipped
        LH, LHtf = self.LHorizontalLine(coords, symbol)
        RH, RHtf = self.RHorizontalLine(coords, symbol)
        UV, UVtf = self.UVerticalLine(coords, symbol)
        DV, DVtf = self.DVerticalLine(coords, symbol)
        UL, ULtf = self.ULDiagonalLine(coords, symbol)
        UR, URtf = self.URDiagonalLine(coords, symbol)
        DL, DLtf = self.DLDiagonalLine(coords, symbol)
        DR, DRtf = self.DRDiagonalLine(coords, symbol)
        createline = LH or RH or UV or DV or UL or UR or DL or DR

        solutions = []

        for solution in [LHtf, RHtf, UVtf, DVtf, ULtf, URtf, DLtf, DRtf]:
            if solution:
                solutions.append(solution)

        return createline, solutions
    #
    # The methods below checks if a line can be created
    # They return boolean if a line can be created by iterating ___ direction from a given location
    # 
    # Tiles are added to a temporary array, until the line can be confirmed as complete, and then they are added to toFlip
    # Once complete, each method will return a solution and the tiles to be flipped, if any
    #
    def LHorizontalLine(self, coords, symbol):
        solution = False
        x = coords[0]
        y = coords[1]
        toFlip = []
        oppsymbol = self.symbols[1 - self.symbols.index(symbol)]
        if self.board.grid[y][x-1].symbol == oppsymbol:
            i = 1
            tempToFlip = []
            while not solution:
                if self.board.grid[y][x-i].symbol == symbol:
                    toFlip = toFlip + tempToFlip
                    solution = True
                tempToFlip.append([x-i, y])
                i+=1
                if self.board.grid[y][x-i].symbol == "X":
                    break
        return solution, toFlip
        
    def RHorizontalLine(self, coords, symbol):
        solution = False
        x = coords[0]
        y = coords[1]
        toFlip = []
        oppsymbol = self.symbols[1 - self.symbols.index(symbol)]
        if self.board.grid[y][x+1].symbol == oppsymbol:
            i = 1
            tempToFlip = []
            while not solution:
                if self.board.grid[y][x+i].symbol == symbol:
                    toFlip = toFlip + tempToFlip
                    solution = True
                tempToFlip.append([x+i, y])
                i+=1
                if self.board.grid[y][x+i].symbol == "X":
                    break
        return solution, toFlip

    def UVerticalLine(self, coords, symbol):
        solution = False
        x = coords[0]
        y = coords[1]
        toFlip = []
        oppsymbol = self.symbols[1 - self.symbols.index(symbol)]
        if self.board.grid[y-1][x].symbol == oppsymbol:
            i = 1
            tempToFlip = []
            while not solution:
                if self.board.grid[y-i][x].symbol == symbol:
                    toFlip = toFlip + tempToFlip
                    solution = True                    
                tempToFlip.append([x, y-i])
                i+=1
                if self.board.grid[y-i][x].symbol == "X":
                    break
        return solution, toFlip

    def DVerticalLine(self, coords, symbol):
        solution = False
        x = coords[0]
        y = coords[1]
        toFlip = []
        oppsymbol = self.symbols[1 - self.symbols.index(symbol)]
        if self.board.grid[y+1][x].symbol == oppsymbol:
            i = 1
            tempToFlip = []
            while not solution:
                if self.board.grid[y+i][x].symbol == symbol:
                    toFlip = toFlip + tempToFlip
                    solution = True                    
                tempToFlip.append([x, y+i])
                i+=1
                if self.board.grid[y+i][x].symbol == "X":
                    break
        return solution, toFlip

    def ULDiagonalLine(self, coords, symbol):
        solution = False
        x = coords[0]
        y = coords[1]
        toFlip = []
        oppsymbol = self.symbols[1 - self.symbols.index(symbol)]
        if self.board.grid[y-1][x-1].symbol == oppsymbol:
            i = 1
            tempToFlip = []
            while not solution:
                if self.board.grid[y-i][x-i].symbol == symbol:
                    toFlip = toFlip + tempToFlip
                    solution = True                    
                tempToFlip.append([x-i, y-i])
                i+=1
                if self.board.grid[y-i][x-i].symbol == "X":
                    break
        return solution, toFlip
        
    def URDiagonalLine(self, coords, symbol):
        solution = False
        x = coords[0]
        y = coords[1]
        toFlip = []
        oppsymbol = self.symbols[1 - self.symbols.index(symbol)]
        if self.board.grid[y-1][x+1].symbol == oppsymbol:
            i = 1
            tempToFlip = []
            while not solution:
                if self.board.grid[y-i][x+i].symbol == symbol:
                    toFlip = toFlip + tempToFlip
                    solution = True                    
                tempToFlip.append([x+i, y-i])
                i+=1
                if self.board.grid[y-i][x+i].symbol == "X":
                    break
        return solution, toFlip
    
    def DLDiagonalLine(self, coords, symbol):
        solution = False
        x = coords[0]
        y = coords[1]
        toFlip = []
        oppsymbol = self.symbols[1 - self.symbols.index(symbol)]
        if self.board.grid[y+1][x-1].symbol == oppsymbol:
            i = 1
            tempToFlip = []
            while not solution:
                if self.board.grid[y+i][x-i].symbol == symbol:
                    toFlip = toFlip + tempToFlip
                    solution = True                    
                tempToFlip.append([x-i, y+i])
                i+=1
                if self.board.grid[y+i][x-i].symbol == "X":
                    break
        return solution, toFlip

    def DRDiagonalLine(self, coords, symbol):
        solution = False
        x = coords[0]
        y = coords[1]
        toFlip = []
        oppsymbol = self.symbols[1 - self.symbols.index(symbol)]
        if self.board.grid[y+1][x+1].symbol == oppsymbol:
            i = 1
            tempToFlip = []
            while not solution:
                if self.board.grid[y+i][x+i].symbol == symbol:
                    toFlip = toFlip + tempToFlip
                    solution = True                    
                tempToFlip.append([x+i, y+i])
                i+=1
                if self.board.grid[y+i][x+i].symbol == "X":
                    break
        return solution, toFlip

    def FlipTiles(self, toFlip, symbol):
        for item in toFlip:
            self.board.grid[item[1]][item[0]].symbol = symbol
        
    def SwitchTurns(self):
        turn = ["Player", "Ai"]
        self.turn = turn[1 - turn.index(self.turn)] # Chooses the other person in the array

    def IsGameOver(self):
        # Checks if the current player has any valid moves       
        if self.turn == "Player":
            if len(self.FindValidMoves(self.symbols[0])) == 0:
                return True
        else:
            if len(self.FindValidMoves(self.symbols[1])) == 0:
                return True
        return False

    def MakeUserMove(self):
        symbol = "●"
        listOfValidMoves = self.FindValidMoves(symbol) # Finds and displays valid moves to the user
        print("\nValid Moves[xy]:", listOfValidMoves)
        # |
        # | Asks for input, checks if valid
        # V
        moveBeingPlayed = True
        while moveBeingPlayed: 
            userInput = False
            while userInput == False:
                userCoords = input("\nPlace a disk [Enter S to Save and Quit]: ")
                if userCoords == "S": # Saves the game and closes
                    self.SaveGame([0,0], self.state)
                    exit()
                try:
                    int(userCoords) == True
                    if len(userCoords) == 2:
                        userInput = True
                    else:
                        print("\nPlease enter a 2-digit number")
                except ValueError:
                    print("\nPlease enter a 2-digit number")
            # |
            # | Checks to see if the move is valid,
            # | then uses that information to carry out a move
            # V
            coords = [int(userCoords[0]), int(userCoords[1])]
            moveIsGood = False
            for move in listOfValidMoves:
                if move.GetCoords() == coords:
                    moveIsGood = move
                    break
            if moveIsGood:
                self.MakeMove(symbol, coords, moveIsGood)
                self.board.PrintBoard()
                moveBeingPlayed = False
            else:
                print("\nInvalid coordinates")

    def MakeMove(self, symbol, coords, move):
        self.board.PlaceDisk(coords, symbol)
        for tile in move.tilesToFlip:
            self.FlipTiles(tile, symbol)

class Move():
    def __init__(self, x, y, tilesToFlip):
        self.x = x
        self.y = y
        self.tilesToFlip = tilesToFlip

    def __repr__(self) -> str:
        return f'{self.x}{self.y}'
    
    def GetCoords(self):
        return [self.x,self.y]
        
class Board():
    def __init__(self):
        self.grid = [] # Makes a blank grid for the board to be generated in

    def GenerateBlankGrid(self):
        for i in range(0,10):
            self.grid.append([])
            for ii in range(0,10):
                self.grid[i].append(Tile([ii, i])) # Each tile is an object and is default blank
    
    def BoardFromArray(self, array): # Converts the array back to the board
        placeInArray = 0
        for i in range(0,10):
            self.grid.append([])
            for ii in range(0,10):
                self.grid[i].append(Tile([ii, i]))
                self.grid[i][ii].symbol = array[placeInArray]
                placeInArray +=1 

    def BoardToArray(self): # Converts the board into an array
        gameBoard = ''
        for i in self.grid:
            for ii in i:                           
                gameBoard+=ii.symbol
        return gameBoard

    def GenerateWalls(self):
        for i in range(0,10):
            if self.grid[i] == self.grid[0]:
                for i in range(0,len(self.grid[i])):
                    self.grid[0][i] == Wall([i,0])
            elif self.grid[i] == self.grid[9]:
                for i in range(0,len(self.grid[i])):                
                    self.grid[i][0] = Wall([0,i])
                    self.grid[i][9] = Wall([9,i])
                    self.grid[0][i] = Wall([i,0])
                    self.grid[9][i] = Wall([i,9])
    
    def GenerateStartBoard(self):
        for i in self.grid:
            for ii in i:
                if ii.location in [[5, 4], [4, 5]]: # Black starting pieces
                    ii.symbol = "○"
                elif ii.location in [[4, 4], [5, 5]]: # White starting pieces
                    ii.symbol = "●"

    def PrintBoard(self):
        print("\n    1 2 3 4 5 6 7 8 ") # Creates numbers for axes
        for i in range(len(self.grid)):
            if i == 0 or i == 9:
                line = " |"
            else:
                line = "{}|".format(i) # Adds the initial vertical lines
            for ii in range(len(self.grid[i])):
                line += "{}|".format(self.grid[i][ii].symbol) # Enters the symbol and another line
            print(line)

    def PlaceDisk(self, location, symbol):
        self.grid[location[1]][location[0]].symbol = symbol

    def CountDisks(self):
        whiteTotal, blackTotal = 0, 0
        for i in self.grid:
            for ii in i:
                if ii.symbol == '●':
                    whiteTotal += 1
                elif ii.symbol == '○':
                    blackTotal += 1
        return whiteTotal, blackTotal

Menu()
