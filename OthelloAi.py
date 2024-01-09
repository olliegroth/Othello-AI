import math
import copy

class Queue(): # Creates the definition of a queue and its functions
    def __init__(self):
        self.queue = []

    def put(self, item):
        self.queue.append(item)
    
    def get(self):
        return self.queue.pop(0)

    def empty(self):
        return self.queue == []
    
    def queue(self):
        return self.queue

    def peak(self):
        return self.queue[0]
    
    def peakLast(self):
        return self.queue[-1]

class SimpleAi:
    def __init__(self, symbol, game, depth=3):
        self.symbol = symbol
        self.oppSymbol = game.symbols[0] if symbol == game.symbols[1] else game.symbols[1]
        self.game = game
        self.game.movesToGetThere = None # a queue of moves to get to a specific state or node on the graph
        self.depth = depth # the depth parameter that determines how many moves ahead SimpleAi will look
        self.workingGame = self.GenerateCleanWorkingGame(self.game) # create a copy of the game instance and initialise the workingGame property

    @staticmethod
    def GenerateStartingGame(game):
        workingGame = copy.deepcopy(game) # Using predefined copy function
        # Reset some properties of the workingGame instance to ensure it is clean
        workingGame.children = []
        workingGame.score = 0
        workingGame.gotoChild = None
        workingGame.movesToGetThere = workingGame.movesToGetThere if game.movesToGetThere else Queue()
        return workingGame

    @staticmethod
    def GenerateCleanWorkingGame(game):
        workingGame = game.copy() # Using custom copy method to only copy specific attributes
        workingGame.movesToGetThere = workingGame.movesToGetThere if game.movesToGetThere else Queue()
        return workingGame

    @staticmethod
    def GenerateAllMoves(game, symbol, depth):
        # Find all valid moves for the given symbol in the given game instance
        listOfValidMoves = game.FindValidMoves(symbol)
        for move in listOfValidMoves:
            coords = move.GetCoords()
            # Create a new game instance by making the current move
            newGame = SimpleAi.GenerateCleanWorkingGame(game)
            newGame.MakeMove(symbol, coords, move)
            # Add the current move to the movesToGetThere property of the new game instance
            newGame.movesToGetThere.put(move)
            # Add the new game instance as a child of the current game instance
            game.children.append(newGame)
            if depth > 0:
                newSymbol = game.symbols[0] if symbol == game.symbols[1] else game.symbols[1]
                gameWithChildren = SimpleAi.GenerateAllMoves(newGame, newSymbol, depth-1)
                # Append the resulting game object to the children list of the input game object
                game.children.append(gameWithChildren)
        return game

    @staticmethod
    def FollowChildren(game):
        if game.children != []:
            # If the game object has children, recursively follow the children until there are no more children
            return SimpleAi.FollowChildren(game.children[game.gotoChild])
        else:
            # If the game object has no children, return a list of moves that led to the game object
            return list(game.movesToGetThere.queue)
    
    @staticmethod
    def IsCornerTile(move):
        # Determine if the move represents a corner tile on the game board
        if move.GetCoords()[0] == 1 and move.GetCoords()[1] == 1 or\
            move.GetCoords()[0] == 1 and move.GetCoords()[1] == 8 or\
            move.GetCoords()[0] == 8 and move.GetCoords()[1] == 1 or\
            move.GetCoords()[0] == 8 and move.GetCoords()[1] == 8:
            return True
        else:
            return False

    @staticmethod
    def MiniMax(game, possSymbol, alpha, beta, depth=0):
        if game.children == []:
            # If the game object has no children, return the score of the game object
            white, black = game.board.CountDisks()
            game.score = white - black if possSymbol == game.symbols[0] else black - white
            return game.score

        if depth % 2 == 0:
            # If the depth is even, the Ai is maximising
            bestScore = -math.inf
            for child in game.children:
                # Find the best score for the Ai
                score = SimpleAi.MiniMax(child, possSymbol, alpha, beta, depth+1)
                if SimpleAi.IsCornerTile(child.movesToGetThere.peakLast()):
                    score = score + 100
                # bestScore = max(score, bestScore)
                if bestScore < score:
                    bestScore = score
                    game.gotoChild = game.children.index(child)
                alpha = max(alpha, bestScore)
                # If the score is greater than or equal to beta, prune the rest of the children
                if bestScore >= beta:
                    break
            return bestScore
        else:
            # If the depth is odd, the opponent is maximising
            worstScore = math.inf
            for child in game.children:
                # Find the worst score for the opponent
                score = SimpleAi.MiniMax(child, possSymbol, alpha, beta, depth+1)
                if SimpleAi.IsCornerTile(child.movesToGetThere.peakLast()):
                    score = score - 200
                if worstScore > score:
                    worstScore = score
                    game.gotoChild = game.children.index(child)
                              
                beta = min(beta, worstScore)
                # If the score is less than or equal to alpha, prune the rest of the children
                if worstScore <= alpha:
                    break
            return worstScore
    
    # This method is responsible for running the Minimax algorithm and returning the best move
    def RunMiniMax(self):
        # Generate a clean working game to work with
        self.workingGame = self.GenerateStartingGame(self.game)
        
        # Generate all possible moves for the current player and depth limit
        self.GenerateAllMoves(self.workingGame, self.symbol, self.depth)
        
        # Find the optimal score using the Minimax algorithm
        optimalScore = self.MiniMax(self.workingGame, self.symbol, -math.inf, math.inf)
        
        # Follow the path of children with the optimal score to find the best move
        result = self.FollowChildren(self.workingGame)
        bestMove = result[0]
        
        # Return the best move and the optimal score
        return bestMove, optimalScore
