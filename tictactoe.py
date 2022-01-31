from math import floor
from math import factorial
from copy import deepcopy
from functools import reduce
import logging
import inspect
import sys

class MyLogger:
   baseline = len(inspect.stack())
   log = logging.getLogger('tictactoe')
   logging.basicConfig()
   log.setLevel(logging.DEBUG)
   active = False

   @classmethod
   def debug(cls, msg, *args):
      if MyLogger.active:
         indent = len(inspect.stack()) - MyLogger.baseline
         logArgs = ['|' * indent + str(msg)]
         logArgs.extend(args)
         MyLogger.log.debug(*logArgs)

   @classmethod
   def on(cls):
      MyLogger.active = True

   @classmethod
   def off(cls):
      MyLogger.active = False


# This trie is used to check for and prevent duplicate subtrees in the minimax tree
class TrieNode:
   def __init__(self, symbol='='):
      self._symbol = symbol
      self._children = {}
      # Node of minimax tree
      self.node = None

   def print(self):
      MyLogger.debug("_symbol=%s", self._symbol)
      if self.node == None:
         MyLogger.debug("node=None")
      else:
         MyLogger.debug("node._board=%s", self.node._board.asString())
      MyLogger.debug("Iterating through _children:")
      for child in self._children:
         child.print()

   # Check if there is a minmax tree node for this board string. If there is, return it.
   # If there isn't, create a new trie node attached to the passed in minimax node and
   # return the passed in minimax node
   def checkMatchAndAdd(self, string, newNode):

      MyLogger.debug('Checking ' + self._symbol + " vs " + string[0])
      if len(string) == 1:
         if self._symbol == string:
            if self.node == None:
               self.node = newNode
            return self.node
         else:
            raise Exception
      else:
         if string[0] == self._symbol:
            child = self._children.get(string[1])
            if child == None:
               child = TrieNode(string[1])
               self._children[string[1]] = child
               MyLogger.debug("Creating new child trie node for symbol %s", string[1])
               return child.checkMatchAndAdd(string[1:], newNode)
            else:
               MyLogger.debug("Found existing child trie node for symbol %s", string[1])
               return child.checkMatchAndAdd(string[1:], newNode)
         else:
            raise Exception("trie node symbol " + self._symbol + " failed to match first char of " + string)




class Board:

   #Extra pound symbols to make columns line up when reading
   layout = \
"""
 #7 | #8 | #9      7 | 8 | 9
-#--|-#--|-#--    ---|---|---
 #4 | #5 | #6      4 | 5 | 6
-#--|-#--|-#--    ---|---|---
 #1 | #2 | #3      1 | 2 | 3
"""
   FILLER = ' '
   SYMBOLS = ('X', 'O')

   def __init__(self, width, height):
      assert(width == height)
      self.width = width
      self.height = height
      self._board = [[Board.FILLER for _ in range(height)] for _ in range(width)]

   def __str__(self):
      layout = Board.layout
      for i in range(self.width):
         for j in range(self.height):
            layout = layout.replace("#" + str(Board.coordToIdx(i, j)), self._board[i][j])
      return layout.replace("#", "")

   def __eq__(self, other):
      return other != None and self._board == other._board

   def __ne__(self, other):
      return not self.__eq__(other)


   def move(self, symbol, idx):
      newBoard = deepcopy(self)
      newBoard._board[newBoard.idxToX(idx)][newBoard.idxToY(idx)] = symbol
      return newBoard

   def getByIdx(self, idx):
      return self.getByCoord(self.idxToX(idx), self.idxToY(idx))

   def getByCoord(self, x, y):
      return self._board[x][y]

   def isFilledByIdx(self, idx):
      return self.isFilled(self.idxToX(idx), self.idxToY(idx))

   def isFilled(self, x, y):
      return self._board[x][y] != Board.FILLER

   def numFilled(self):
      count = 0
      for idx in range(1, (self.width * self.height) + 1):
         if self.isFilledByIdx(idx):
            count += 1
      return count

   def asString(self):
      result = ""
      for i in range(self.width * self.height):
         c = self.getByIdx(i + 1)
         result += (c if c != ' ' else '-')
      return result

   def asBase3(self):
      charToNum = { \
         '-': "0", \
         ' ': "0", \
         'X': "1", \
         'O': "2"  \
      }
      result = ""
      s = self.asString()
      for i in range(len(s), 0, -1):
         c = self.getByIdx(i)
         result = charToNum[c] + result
      return result

   def asInt(self):
      return int(self.asBase3(), 3)

   def _genIsVertWinner(self):
      counters = {}
      for s in Board.SYMBOLS:
         counters[s] = [0 for i in range(self.width)]
      result = False

      # Count if this square is part of a column 3 in a row
      def isVertWinner(x, y):
         nonlocal result
         nonlocal counters

         symbol = self._board[x][y]
         if (not result):
            if self.isFilled(x, y):
               counters[symbol][x] += 1
               if counters[symbol][x] == self.height:
                  result = True
                  return True
         return result
      return isVertWinner

   def _genIsHorizWinner(self):
      counters = {}
      for s in Board.SYMBOLS:
         counters[s] = [0 for i in range(self.height)]
      result = False

      # Count if this square is part of a row 3 in a row
      def isHorizWinner(x, y):
         nonlocal result
         nonlocal counters

         symbol = self._board[x][y]
         if (not result):
            if self.isFilled(x, y):
               counters[symbol][y] += 1
               if counters[symbol][y] == self.width:
                  result = True
                  return True
         return result
      return isHorizWinner

   def _genIsDiagWinner(self):
      counters = {}
      for s in Board.SYMBOLS:
         #'FS' == forward slash
         #'BS' == back slash
         counters[s] = {\
            'FS' : 0,\
            'BS' : 0\
         }
      result = False

      # Count if this square is part of a diagonal 3 in a row
      def isDiagWinner(x, y):
         nonlocal counters
         nonlocal result

         symbol = self._board[x][y]
         if (not result):
            if self.isFilled(x, y):
               #Back slash diagonal
               if x == y:
                  counters[symbol]['BS'] += 1
                  if counters[symbol]['BS'] == self.height:
                     result = True
                     return result
               #Forward slash diagonal
               if x + y == self.height - 1:
                  counters[symbol]['FS'] += 1
                  if counters[symbol]['FS'] == self.height:
                     result = True
                     return result
         return result

      return isDiagWinner

   # If the game is over, returns the winning symbol "X" or "O"
   # Returns "C" if a cat's game
   def getWinner(self):
      #These are counters that store their counted values in closures
      isVertWinner = self._genIsVertWinner()
      isHorizWinner = self._genIsHorizWinner()
      isDiagWinner = self._genIsDiagWinner()

      foundEmptySpace = False
      for x in range(self.width):
         for y in range(self.height):
            if self.isFilled(x, y):
               if (isVertWinner(x, y) or \
                  isHorizWinner(x, y) or \
                  isDiagWinner(x, y)):
                  return self._board[x][y]
            else:
               foundEmptySpace = True

      if not foundEmptySpace:
         # Cat's game
         return 'C'
      else:
         return None

   # Makes a iterator through all valid moves for this board
   def makeMoveIter(self, symbol):
      if self.getWinner() != None:
         return
      else:
         for idx in range(1, (self.width * self.height)+1):
            if (not self.isFilledByIdx(idx)):
               yield self.move(symbol, idx)
         return

   # Returns single move difference between this board, and a board 1 move later
   def diffBoard(self, otherBoard):
      a = self.asString()
      b = otherBoard.asString()

      symbol = None
      moveIdx = None
      for i in range(len(a)):
         if a[i] != b[i]:
            if (a[i] == "-" or a[i] == " ") and \
                  (symbol == None and moveIdx == None):
               symbol = b[i]
               moveIdx = i + 1
            else:
               raise Exception("Boards not consecutive: (" + a + ", " + b + ")")

      return symbol, moveIdx

   @staticmethod
   def idxToX(idx):
      return (idx - 1) % 3

   @staticmethod
   def idxToY(idx):
      # Match the indices up with the number keypad
      return -(floor((idx - 1) / 3) - 1) + 1

   @staticmethod
   def coordToIdx(x, y):
      return 3 * (-(y - 1) + 1) + x + 1


class Node:
   count = 0
   num = 0
   depth = 0
   levelCount = dict.fromkeys(range(1, 10), 0)

   def __init__(self, board, turn, trie):
      self._board = board

      # We are reusing nodes, but it's okay to store turn here because the board
      # configuration will always guarantee the same turn even if the path to it
      # is different

      # The turn of the next move
      # turn==1 when max's (computer's) turn
      # turn==-1 when min's (user's) turn
      self._turn = turn
      self.children = []
      self._trie = trie
      self._symbol = Game.SCORE_TO_SYMBOL[turn]
      self._minBound = -999999
      self._maxBound = 999999

   def __eq__(self, other):
      return other != None and self._board == other._board and self._turn == other._turn

   def __ne__(self, other):
      return not self.__eq__(other)

   def isFinished(self):
      return self._board.getWinner() == None

   def getBestMoveIdx(self):
      _, board = self.getBestMove()
      symbol, moveIdx = self._board.diffBoard(board)
      assert(symbol == Game.SCORE_TO_SYMBOL[self._turn])
      return moveIdx


   def getBestMove(self, minBound=-999999, maxBound=999999):
      if self._turn == 1:
         score, board = self.getBestMoveScoreMax(minBound, maxBound)
         return score, board
      elif self._turn == -1:
         score, board = self.getBestMoveScoreMin(minBound, maxBound)
         return score, board
      else:
         raise Exception

   def getBestMoveScoreMin(self, minBound=-999999, maxBound=999999):
      MyLogger.debug("getBestMoveScoreMin with [" + str(minBound) + ", " + str(minBound) + "]")
      MyLogger.debug("looking at board " + self._board.asString())
      winner = self._board.getWinner()
      if winner != None:
         MyLogger.debug("Winner '%s' returning score %s", winner, str(Game.SYMBOL_TO_SCORE))
         return Game.SYMBOL_TO_SCORE[winner], None

      score = 999999
      bestChild = None
      for child in self.children:
         MyLogger.debug("Child %s,", child._board.asString())
         MyLogger.debug("score is " + str(score))
         MyLogger.debug(id(self))

         result,_ = child.getBestMoveScoreMax(minBound, maxBound)
         MyLogger.debug("Comparing score %s with result %s", str(score), str(result))

         if (score > result):
            score = result
            bestChild = child

         MyLogger.debug("Could this be it? %s", str(score))

         MyLogger.debug("minBound: %s", str(minBound))
         if score <= minBound:
            return score, bestChild._board
         maxBound = min(maxBound, score)
      MyLogger.debug("Best board child: %s", bestChild._board.asString())
      return score, bestChild._board


   def getBestMoveScoreMax(self, minBound=-999999, maxBound=999999):
      MyLogger.debug("getBestMoveScoreMax with [" + str(minBound) + ", " + str(maxBound) + "]")
      MyLogger.debug("looking at board " + self._board.asString())
      winner = self._board.getWinner()
      if winner != None:
         MyLogger.debug("Found game %s winner: %s", winner, self._board.asString())
         return Game.SYMBOL_TO_SCORE[winner], None

      score = -999999
      bestChild = None
      MyLogger.debug("Iterating thru %i children", len(self.children))
      for child in self.children:
         MyLogger.debug("Child %s,", child._board.asString())
         result,_ = child.getBestMoveScoreMin(minBound, maxBound)
         MyLogger.debug("Comparing score %s with result %s", str(score), str(result))
         if score < result:
            score = result
            bestChild = child

         if score >= maxBound:
            return score, bestChild._board
         minBound = max(minBound, score)
      MyLogger.debug("Best board child: %s", bestChild._board)
      return score, bestChild._board



   def getChildNodeByBoard(self, board):
      MyLogger.debug("Looking for child %s of board %s by boardString", board.asString(), self._board.asString())
      nodes = [None]
      nodes = [node for node in self.children if node._board.asString() == board.asString()]
      MyLogger.debug("Found children %s", str(nodes))
      if len(nodes) > 1:
         raise Exception
      return nodes[0]

   # Create Minimax tree
   def genTree(self):
      Node.count += 1
      Node.depth += 1
      Node.levelCount[Node.depth] += 1
      moveIter = self._board.makeMoveIter(Game.SCORE_TO_SYMBOL[self._turn])
      i = 0
      MyLogger.debug('Generating tree for board %s', self._board.asString())
      for b in moveIter:
         MyLogger.debug('Attempting to add new board %s', b.asString())
         i += 1
         newChild = Node(b, -1 * self._turn, self._trie)

         # Check for duplicates and reuse subtrees if possible
         # The node we get back will be the same node or a new one, depending
         # on if the tree already has that board configuration.
         # Add "=" to the beginning so all boards share a root
         child = self._trie.checkMatchAndAdd("=" + b.asString(), newChild)
         self.children.append(child)

         # Only need to generate subtree if this is a new node
         if not child is newChild:
            MyLogger.debug("Child %s already exists", child._board.asString())
         else:
            Node.num += 1
            MyLogger.debug("Child %s is new", child._board.asString())
            child.genTree()
      Node.count -= 1
      Node.depth -= 1

class Game:
   MAX_SCORE = 1
   MIN_SCORE = -1
   CAT_SCORE = 0

   SCORE_TO_SYMBOL = { \
      MIN_SCORE:'X', \
      MAX_SCORE:'O', \
      CAT_SCORE:'C'
   }

   SYMBOL_TO_SCORE = { \
      'X': MIN_SCORE, \
      'O': MAX_SCORE, \
      'C': CAT_SCORE \
   }

   SYMBOL_TO_WIN_MESSAGE = { \
      "X": "You Win!", \
      "O": "The Computer Wins!", \
      "C": "Cat's Game! =^.^=" \
   }

   def checkWinner(b):
      winner = b.getWinner()
      if winner != None:
         print(b)
         print(Game.SYMBOL_TO_WIN_MESSAGE[winner] + "\n")
         exit(0)

   def start():
      print("\nWelcome to Tic-Tac-Toe World")
      print("Where your wildest Tic-Tac-Toe-related dreams")
      print("are just a minimax search away! (It's true.)")

      currBoard = Board(3, 3)
      firstTurn = True

      while (True):

         moveIdx = ""
         while (not moveIdx.isdigit() or \
               int(moveIdx) < 1 or \
               int(moveIdx) > 9 or \
               currBoard.isFilledByIdx(int(moveIdx))):

            print(currBoard)
            moveIdx = input("Enter a move (1-9): ")

         moveIdx = int(moveIdx)
         currBoard = currBoard.move('X', moveIdx)
         Game.checkWinner(currBoard)

         if firstTurn:
            firstTurn = False

            MyLogger.debug('Setting up trees')
            trie = TrieNode()
            root = Node(currBoard, 1, trie)
            trie.node = root
            currNode = root

            print("Creating search tree...")
            root.genTree()

         else:
            currNode = currNode.getChildNodeByBoard(currBoard)

         MyLogger.debug("Current board is %s, looking for best move...", currNode._board.asString())

         print("Searching for best move...")

         moveIdx = currNode.getBestMoveIdx()
         MyLogger.debug("Best move found: %i", moveIdx)

         MyLogger.debug("Board before move: %s", currBoard.asString())
         currBoard = currBoard.move('O', moveIdx)
         MyLogger.debug("Board after move: %s", currBoard.asString())

         Game.checkWinner(currBoard)
         currNode = currNode.getChildNodeByBoard(currBoard)

# Tests {{{

def test():
   testIdxToX()
   testIdxToY()
   testCoordToIdx()
   testMove()
   testBoardInit()
   testGetByCoord()
   testBoardPrint()
   testGetWinnerVert()
   testGetWinnerHoriz()
   testGetWinnerDiagFS()
   testGetWinnerDiagBS()
   testGetWinnerCats()
   testAsString()
   testAsBase3()
   testTrieMatchAndAddFirst()
   testTrieMatchAndAddFullerGame()
   testDiffBoard()
   testChoose()
   testLogger()
   testGenTree()

def testDiffBoard():
   b0 = Board(3, 3)
   b1 = b0.move('X', 1)
   assert(('X', 1) == b0.diffBoard(b1))

   b2 = b1.move('O', 8)
   assert(('O', 8) == b1.diffBoard(b2))

   b3 = b2.move('X', 2)
   assert(('X', 2) == b2.diffBoard(b3))

   b4 = b3.move('O', 5)
   assert(('O', 5) == b3.diffBoard(b4))

   b5 = b4.move('X', 9)
   assert(('X', 9) == b4.diffBoard(b5))

def testTrieMatchAndAddFirst():
   b0 = Board(3, 3)
   t1 = TrieNode()
   b1 = b0.move('X', 1)
   n1 = Node(b1, 1, t1)
   t1.node = n1

   b0b = Board(3, 3)
   b1b = b0b.move('X', 1)
   n1b = Node(b1b, 1, t1)

   assert(not b0b is b0)
   assert(not b1b is b1)
   assert(not n1b is n1)

   print('test')
   resultNode = t1.checkMatchAndAdd("=" + b1.asString(), n1)
   assert(None != resultNode)
   assert(n1 is resultNode)
   assert(not n1b is resultNode)

   print('test1')
   resultNode = t1.checkMatchAndAdd("=" + b1.asString(), n1b)
   assert(None != resultNode)
   assert(n1 is resultNode)
   assert(not n1b is resultNode)

def checkTrieMatching(trie, node1, node2):
   assert(not node1 is node2)

   #First time should return node passed in
   resultNode = trie.checkMatchAndAdd("=" + node1._board.asString(), node1)
   assert(None != resultNode)
   assert(node1 is resultNode)
   assert(not node2 is resultNode)

   #Second time should still return first node
   resultNode = trie.checkMatchAndAdd("=" + node1._board.asString(), node2)
   assert(None != resultNode)
   assert(node1 is resultNode)
   assert(not node2 is resultNode)

def testTrieMatchAndAddFullerGame():
   t1 = TrieNode()

   b0 = Board(3, 3)
   b1 = b0.move('X', 1)
   n1 = Node(b1, -1, t1)
   t1.node = n1

   b2 = b1.move('O', 5) \
         .move('X', 2) \
         .move('O', 6) \
         .move('X', 7) \
         .move('O', 8) \
         .move('X', 9)
   n2 = Node(b2, 1, t1)

   b2b = b1.move('O', 5) \
         .move('X', 2) \
         .move('O', 6) \
         .move('X', 7) \
         .move('O', 8) \
         .move('X', 9)
   n2b = Node(b2b, 1, t1)

   print('test3')
   checkTrieMatching(t1, n2, n2b)

   b3 = b1.move('O', 5) \
         .move('X', 2) \
         .move('X', 6) \
         .move('O', 7) \
         .move('O', 8) \
         .move('X', 9)
   n3 = Node(b3, 1, t1)

   b3b = b1.move('O', 5) \
         .move('X', 2) \
         .move('X', 6) \
         .move('O', 7) \
         .move('O', 8) \
         .move('X', 9)
   n3b = Node(b3b, 1, t1)

   print('test4')
   checkTrieMatching(t1, n3, n3b)

   b4 = b1.move('O', 5) \
         .move('X', 2) \
         .move('X', 6) \
         .move('O', 7) \
         .move('O', 8) \
         .move('O', 9)
   n4 = Node(b4, 1, t1)

   b4b = b1.move('O', 5) \
         .move('X', 2) \
         .move('X', 6) \
         .move('O', 7) \
         .move('O', 8) \
         .move('O', 9)
   n4b = Node(b4b, 1, t1)

   print('test5')
   checkTrieMatching(t1, n4, n4b)

   b5 = b1.move('X', 5) \
         .move('X', 2) \
         .move('X', 6) \
         .move('O', 7) \
         .move('O', 8) \
         .move('O', 9)
   n5 = Node(b5, 1, t1)

   b5b = b1.move('X', 5) \
         .move('X', 2) \
         .move('X', 6) \
         .move('O', 7) \
         .move('O', 8) \
         .move('O', 9)
   n5b = Node(b5b, 1, t1)

   print('test6')
   checkTrieMatching(t1, n5, n5b)


def testAsBase3():
   board = Board(3, 3)
   board = board.move('X', 1)
   board = board.move('X', 2)
   board = board.move('O', 4)
   board = board.move('O', 6)
   board = board.move('X', 8)
   board = board.move('O', 9)
   assert("110202012" == board.asBase3())
   print("success!")

def testAsString():
   board = Board(3, 3)
   board = board.move('X', 1)
   board = board.move('X', 2)
   board = board.move('O', 4)
   board = board.move('O', 6)
   board = board.move('X', 8)
   board = board.move('O', 9)
   assert("XX-O-O-XO" == board.asString())
   print("success!")

def choose(n, r):
   if n < r:
      raise Exception
   return factorial(n) / (factorial(r) * factorial(n - r))

def testChoose():
   assert(15 == choose(6, 2))
   assert(1 == choose(6, 6))
   assert(1 == choose(6, 0))
   assert(126 == choose(9, 5))
   print("success!")

def testGenTree():
   b0 = Board(3, 3)
   t1 = TrieNode()
   b1 = b0.move('X', 1)
   root = Node(b1, 1, t1)
   t1.node = root

   print('Generating tree:')
   print(Node.levelCount)
   root.genTree()
   print('Num nodes: ' + str(Node.num))
   print('levels:')
   print(Node.levelCount)
   maxNodes = 0

   #Number of max nodes is much smaller because of trie use
   #Calculate number of nodes if all games played to a full board
   #for i in range(1,10):
   #  maxNodes += (factorial(9) / factorial(i))

   maxNodes = 3**9

   #Should have less than this number of nodes
   #assert(maxNodes > Node.num)
   print(str(maxNodes))

   #Calculate the number of
"""
   numWins = 0
   for turn in range(3, 10):
      numWins += 6 *

   expectedMovesNum = 0
   def preFun(node):
      nonlocal expectedMovesNum
      assert(expectedMovesNum == node.numFilled())
      expectedMovesNum += 1

   def postFun(node):
      nonlocal expectedMovesNum
      print(node)
      expectedMovesNum -= 1

   iterTree(root, preFun, postFun)
"""


def iterTree(node, pre, post):
   if pre: pre(node)
   for child in node.children:
      iterTree(child)
   if post: post(node)


def testGetByCoord():
   board = Board(3, 3)
   board = board.move("O", 7)
   assert("O" == board.getByCoord(0, 0))

   board = board.move("X", 2)
   assert("X" == board.getByCoord(1, 2))
   print("success!")

def testBoardInit():
   board = Board(3, 3)
   assert(3 == board.width)
   assert(3 == board.height)
   assert(3 == len(board._board))
   assert(3 == len(board._board[0]))
   print("success!")


def testMove():
   board = Board(3, 3)

   board = board.move("X", 4)
   assert("X" == board.getByIdx(4))

   board = board.move("O", 1)
   assert("O" == board.getByIdx(1))

   board = board.move("X", 9)
   assert("X" == board.getByIdx(9))

   print("success!")



def testIdxToY():
   assert(2 == Board.idxToY(1))
   assert(2 == Board.idxToY(2))
   assert(2 == Board.idxToY(3))
   assert(1 == Board.idxToY(4))
   assert(1 == Board.idxToY(5))
   assert(1 == Board.idxToY(6))
   assert(0 == Board.idxToY(7))
   assert(0 == Board.idxToY(8))
   assert(0 == Board.idxToY(9))
   print("success!")

def testIdxToX():
   assert(0 == Board.idxToX(1))
   assert(1 == Board.idxToX(2))
   assert(2 == Board.idxToX(3))
   assert(0 == Board.idxToX(4))
   assert(1 == Board.idxToX(5))
   assert(2 == Board.idxToX(6))
   assert(0 == Board.idxToX(7))
   assert(1 == Board.idxToX(8))
   assert(2 == Board.idxToX(9))
   print("success!")

def testCoordToIdx():
   assert(7 == Board.coordToIdx(0, 0))
   assert(8 == Board.coordToIdx(1, 0))
   assert(9 == Board.coordToIdx(2, 0))
   assert(4 == Board.coordToIdx(0, 1))
   assert(5 == Board.coordToIdx(1, 1))
   assert(6 == Board.coordToIdx(2, 1))
   assert(1 == Board.coordToIdx(0, 2))
   assert(2 == Board.coordToIdx(1, 2))
   assert(3 == Board.coordToIdx(2, 2))
   print("success!")

def testBoardPrint():
   b = Board(3, 3)
   print(b)
   b = b.move('X', 3);
   print(b)
   b = b.move('O', 5);
   print(b)
   b = b.move('X', 9);
   print(b)
   b = b.move('O', 4);
   print(b)
   b = b.move('X', 1);
   print(b)

def testGetWinnerVert():
   b = Board(3, 3)
   b = b.move('X', 7)
   b = b.move('O', 4)
   b = b.move('X', 1)
   assert(None == b.getWinner())
   b = b.move('X', 9)
   assert(None == b.getWinner())
   b = b.move('O', 8)
   assert(None == b.getWinner())
   b = b.move('O', 5)
   assert(None == b.getWinner())
   b = b.move('O', 2)
   assert('O' == b.getWinner())
   print("success!")

def testGetWinnerHoriz():
   b = Board(3, 3)
   b = b.move('X', 7)
   b = b.move('O', 4)
   b = b.move('X', 1)
   assert(None == b.getWinner())
   b = b.move('X', 9)
   assert(None == b.getWinner())
   b = b.move('O', 2)
   assert(None == b.getWinner())
   b = b.move('O', 5)
   assert(None == b.getWinner())
   b = b.move('X', 8)
   assert('X' == b.getWinner())
   print("success!")

def testGetWinnerDiagBS():
   b = Board(3, 3)
   b = b.move('O', 7)
   b = b.move('O', 4)
   b = b.move('X', 1)
   assert(None == b.getWinner())
   b = b.move('X', 9)
   assert(None == b.getWinner())
   b = b.move('O', 2)
   assert(None == b.getWinner())
   b = b.move('O', 5)
   assert(None == b.getWinner())
   b = b.move('O', 3)
   assert('O' == b.getWinner())
   print("success!")

def testGetWinnerDiagFS():
   b = Board(3, 3)
   b = b.move('O', 7)
   b = b.move('O', 4)
   b = b.move('X', 1)
   assert(None == b.getWinner())
   b = b.move('X', 9)
   assert(None == b.getWinner())
   b = b.move('O', 2)
   assert(None == b.getWinner())
   b = b.move('X', 5)
   assert('X' == b.getWinner())
   print("success!")

def testGetWinnerCats():
   b = Board(3, 3)
   b = b.move('O', 7)
   assert(None == b.getWinner())
   b = b.move('X', 4)
   assert(None == b.getWinner())
   b = b.move('X', 1)
   assert(None == b.getWinner())
   b = b.move('X', 9)
   assert(None == b.getWinner())
   b = b.move('O', 2)
   assert(None == b.getWinner())
   b = b.move('O', 5)
   assert(None == b.getWinner())
   b = b.move('O', 6)
   assert(None == b.getWinner())
   b = b.move('X', 8)
   assert(None == b.getWinner())
   b = b.move('X', 3)
   assert('C' == b.getWinner())
   print('success!')

def testLogger(count=None):
   print('testing')
   if count == None:
      print('testing2')
      count = 0
      MyLogger.debug("This is a test #%i, '%s'", count, str(count))
      testLogger(count)
      MyLogger.debug("And back up...")
   elif count < 6:
      print('testing2')
      count += 1
      MyLogger.debug("This is a test #%i, '%s'", count, str(count))
      testLogger(count)
      MyLogger.debug("And back up...")

# }}}

if __name__ == "__main__":

   if len(sys.argv) > 1 and sys.argv[1] == "-t":
      test()
   else:
      Game.start(*sys.argv[1:])

#TODO faded numbers vs X and Os


# vim:fdm=marker
