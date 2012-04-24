#!/usr/bin/python

import pygame, sys, os
import math
import itertools
import random
from pygame.locals import *

#load_image function
#@param name the file name of the image
#@param colorkey the transparent color in the image
#@return the image surface
def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname) #load a surface
    except pygame.error, message:
        print 'Cannot load image:', name
        raise SystemExit, message
    image = image.convert() #convert pixel format
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL) #the transparent color
    return image

#Piece class represents a piece on the board
class Piece(pygame.sprite.Sprite):
    #__init__ method
    #@param _player the player for which the piece belongs
    #@param _x the starting x position
    #@param _y the starting y position
    def __init__(self, _player, _x, _y):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.add(allspritesGroup)
        self.image = pieceImg[_player]
        self.rect = self.image.get_rect()
        self.grabbed = False
        self.player = _player
        self.position = -1 #position on the board
        self.paths = []
        self.lost = False #true if the piece has been lost and removed from the board
        self.xyPrevious = (_x, _y) #previous position before grabbing
        self.xy = (_x, _y) #x y coordinates
        self.dest = self.xy
        self.moving = False
        self.jumpTo(self.xy)

    #remove method
    #remove the piece from the board
    def remove(self):
        self.position = -1
        self.lost = True
        self.moving = True
        self.dest = ((800, 800))

    #findBestPath method
    #@param _dest the destination position
    #@return the shortest path from position to _dest as a list or an empty
    #list if there is no path
    def findBestPath(self, _dest):
        self.paths = []
        self.findPaths([self.position], _dest)
        if self.paths:
            return random.sample(filter(lambda x: len(x) == min([len(i) for i in self.paths]), self.paths), 1)[0]
        return []

    #findPaths method
    #finds all simple paths from position to _dest and adds them to the _path list
    #@param _path the path so far
    #@param _dest the destination position
    def findPaths(self, _path, _dest):
        if _path[-1] == _dest:
            self.paths += [_path]
        for i in filter(lambda x: board[x] == 0, neighbors[_path[-1]]):
            if not i in _path:
                self.findPaths(_path + [i], _dest)

    #getOpenNeighbors method
    #@return a list of open neighbor positions
    def getOpenNeighbors(self):
        return filter(lambda x: board[x] == 0, neighbors[self.position])
    
    #jumpTo method
    #@param (x, y) the new x,y position
    def jumpTo(self, (x, y)):
        self.xy = (x, y)

    #update method
    #updates the piece every step of the game
    def update(self):
        if self.grabbed:
            self.jumpTo(pygame.mouse.get_pos())
        if self.moving:
            d = point_direction(self.xy, self.dest)
            s = min(20, point_distance(self.xy, self.dest) / 8)
            self.jumpTo((self.xy[0] + (math.sin(d) * s), self.xy[1] - (math.cos(d) * s)))
            if point_distance(self.xy, self.dest) < 1:
                self.moving = False
        self.rect.center = (self.xy[0], self.xy[1]) #move rect to xy

#point_direction function
#@param (x1, y1) the first position
#@param (x2, y2) the second position
#@return the direction in radians from (x1,y1) to (x2,y2)
def point_direction((x1, y1), (x2, y2)):
    return math.atan2(x2 - x1, y1 - y2)

#point_distance function
#@param (x1, y1) the first position
#@param (x2, y2) the second position
#@return the distance from (x1,y1) to (x2,y2)
def point_distance((x1, y1), (x2, y2)):
    return math.sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))
        
#returns true if the position is part of a mill for player
#isMill function
#@param _pos the position
#@param _player the player, either 1 or 2
#@return the _pos is part of a mill or not
def isMill(_pos, _player):
    if board[_pos] != 0: #there's a piece here
        if board[_pos].player == _player: #the piece belongs to this player
            if board[mills[_pos][0][0]] != 0 and board[mills[_pos][0][1]] != 0: #there are pieces at the 2 other intersections
                if board[mills[_pos][0][0]].player == _player and board[mills[_pos][0][1]].player == _player:
                    return True
            if board[mills[_pos][1][0]] != 0 and board[mills[_pos][1][1]] != 0: #there are pieces at the 2 other intersections
                if board[mills[_pos][1][0]].player == _player and board[mills[_pos][1][1]].player == _player:
                    return True
    return False

#canMove method
#returns true if player can slide any pieces
#@param _player the player
#@return true if the player can make a move
def canMove(_player):
    for i in pieces:
        if i.player == _player and i.position != -1:
            for p in neighbors[i.position]:
                if board[p] == 0:
                    return True
    return False

#allMills function                
#returns true if all pieces on the board for player are part of mills
#@param _player the player
#@return true if all _player's pieces are part of mills
def allMills(_player):
    for i in pieces:
        if i.player == _player and i.position != -1:
            if not isMill(i.position, _player):
                return False
    return True

#isLegalMove function
#@param _from the starting position
#@param _to the endint position
#@return true if _from to _to is connected by a line
def isLegalMove(_from, _to):
    if (_from, _to) in [(0, 7), (7, 0), (8, 15), (15, 8), (16, 23), (23, 16)]:
        return True
    if (_from, _to) in [(7, 8), (8, 7), (15, 16), (16, 15)]:
        return False
    if _from % 2 == 1:
        if abs(_to - _from) == 8:
            return True
    if abs(_to - _from) == 1:
        return True
    return False

#getAllMoves function
#@param _player the player
#@param flying if _player is in the flying stage
#@return a list of possible moves for player as [piece, destination]
def getAllMoves(_player, flying):
    moves = []
    if flying:
        emptyIntersections = filter(lambda x: board[x] == 0, range(24))
        for i in pieces:
            if i.player == _player and not i.lost and i.position != -1:
                for x in emptyIntersections:
                    moves += [[i, x]]
    else:
        for i in pieces:
            if i.player == _player and not i.lost and i.position != -1:
                for x in i.getOpenNeighbors():
                    moves += [[i, x]]
    return moves

#getPiecesRemaining function
#@param _player the player
#@return the number of pieces remaining for player
def getPiecesRemaining(_player):
    total = 0
    for i in pieces:
        if i.player == _player and i.lost:
            total += 1
    return 9 - total

#getIntersectionValue function
#@param _player the player1Group
#@param _pos the position on the boardImg
#@return a value for an open intersection corresponding to how valuable the spot is for player
def getIntersectionValue(_player, _pos):
    value = 0
    if _pos in [1, 3, 5, 7, 17, 19, 21, 23]: #edge
        value += 1
    elif _pos in [9, 11, 13, 15]: #intersection
        value += 2

    #check if adjacent intersections can be mills
    if board[_pos] != 0:
        if board[_pos].player == 2:
            for i in filter(lambda x: board[x] == 0, neighbors[_pos]):
                if board[mills[i][0][0]] != 0 and board[mills[i][0][1]] != 0 and not (_pos in mills[i][0]):
                    if board[mills[i][0][0]].player == _player and board[mills[i][0][1]].player == _player: #we can make a mill
                        value -= 50
                elif board[mills[i][1][0]] != 0 and board[mills[i][1][1]] != 0 and not (_pos in mills[i][1]):
                    if board[mills[i][1][0]].player == _player and board[mills[i][1][1]].player == _player: #we can make a mill
                        value -= 50
        if isMill(_pos, _player): #this is a mill
            value -= 7

    if board[mills[_pos][0][0]] != 0 and board[mills[_pos][0][1]] != 0:
        if board[mills[_pos][0][0]].player == _player and board[mills[_pos][0][1]].player == _player: #we can make a mill
            value += 7
        elif board[mills[_pos][0][0]].player == _player % 2 + 1 and board[mills[_pos][0][1]].player == _player % 2 + 1: #block a mill
            value += 7
    elif board[mills[_pos][1][0]] != 0 and board[mills[_pos][1][1]] != 0:
        if board[mills[_pos][1][0]].player == _player and board[mills[_pos][1][1]].player == _player: #we can make a mill
            value += 7
        elif board[mills[_pos][1][0]].player == _player % 2 + 1 and board[mills[_pos][1][1]].player == _player % 2 + 1: #block a mill
            value += 7
    if board[mills[_pos][0][0]] != 0:
        if board[mills[_pos][0][0]].player == _player:
            value += 1
    if board[mills[_pos][0][1]] != 0:
        if board[mills[_pos][0][1]].player == _player:
            value += 1
    if board[mills[_pos][1][0]] != 0:
        if board[mills[_pos][1][0]].player == _player:
            value += 1
    if board[mills[_pos][1][1]] != 0:
        if board[mills[_pos][1][1]].player == _player:
            value += 1
    if len(filter(lambda x: board[x].player == 1, filter(lambda x: board[x] != 0, neighbors[_pos]))) > 1:
        value += 3
    return value

#getPathValue function
#@param _path the path as a list
#@return a value for the path corresponding to how good this path is for player 2
def getPathValue(_path):
    value = getIntersectionValue(2, _path[1]) - getIntersectionValue(2, _path[0])
    for i in _path[2:]:
        value += (getIntersectionValue(2, i) - 3)
    return value

#calcPieceToRemove()
#return the best piece for player 2 to remove
def calcPieceToRemove():
    possiblePieces = filter(lambda x: x != -1, [i.position for i in pieces[:9]]) #positions of player1 pieces on the board
    if not allMills(1):
        possiblePieces = filter(lambda x: not isMill(x, 1), possiblePieces) #exclude pieces in mills
    values = [getIntersectionValue(2, i) for i in possiblePieces] #values for possible pieces
    return board[possiblePieces[random.sample(filter(lambda x: values[x] == max(values), range(len(possiblePieces))), 1)[0]]]

#calcBestMove function
#@param stage the current stage
#@return the best move for player as a list [piece, destination]
def calcBestMove(stage):
    if stage == 1: #placing stage
        piece = filter(lambda x: x.player == 2 and x.position == -1 and not x.lost, pieces)[0] #the first unplaced piece for player 2
        values = [getIntersectionValue(2, i) for i in range(24)] #get values for all intersections
        destination = []
        emptyIntersections = filter(lambda x: board[x] == 0, range(24))
        maxValue = 0
        for i in emptyIntersections: #find the highest valued empty intersections
            if values[i] > maxValue:
                maxValue = values[i]
                destination = [i]
            elif values[i] == maxValue:
                destination += [i]
        return [piece, random.sample(destination, 1)[0]]
    elif stage == 2: #sliding stage
        emptyIntersections = filter(lambda x: board[x] == 0, range(24))
        paths = []
        #find shortest paths from all pieces to all empty intersections
        for d in emptyIntersections:
            paths += filter(lambda x: x != [], [p.findBestPath(d) for p in filter(lambda x: not x.lost and x.position != -1, pieces[9:])])
        if paths != []:
            values = [getPathValue(i) for i in paths] #values of the paths
            paths = random.sample([paths[i] for i in filter(lambda x: values[x] == max(values), range(len(paths)))], 1)[0]
            return [board[paths[0]], paths[1]]
        return []
    else: #flying stage
        moves = getAllMoves(2, True)
        values = [getIntersectionValue(2, i[1]) - getIntersectionValue(2, i[0].position) for i in moves]
        return moves[random.sample(filter(lambda x: values[x] == max(values), range(len(moves))), 1)[0]]
        

def main():
    mouseRect = 0
    selectedPiece = 0
    turn = 1 #player1 turn
    piecesToPlay = 18 #pieces left to be placed on the board
    removePiece = False #if we made a mill and are choosing a piece to remove
    removedPiece = False #we just removed a piece
    stage = 0 #0 = choose # of players, 1 = in game, 2 = play again?
    players = 1 #number of human players
    movingPiece = 0 # the piece that is moving, if there is one
    
    while True:
        clock.tick(30)
        if players == 1 and turn == 2 and stage != 2: # do AI stuff
            if movingPiece != 0: #a piece is moving
                if not movingPiece.moving:
                    movingPiece = 0
            else:
                if removePiece:
                    bestMove = calcPieceToRemove()
                    board[bestMove.position] = 0
                    bestMove.remove()
                    removePiece = False
                    turn = turn % 2 + 1 #switch turns
                    if getPiecesRemaining(turn) < 3 or (piecesToPlay <= 1 and getPiecesRemaining(turn) > 3 and not canMove(turn)):
                        stage = 2 #game over
                else:
                    if piecesToPlay > 0:
                        bestMove = calcBestMove(1)
                    elif getPiecesRemaining(2) > 3:
                        bestMove = calcBestMove(2)
                    else:
                        bestMove = calcBestMove(3)
                    if bestMove != []: #otherwise player2 is trapped
                        movingPiece = bestMove[0]
                        movingPiece.moving = True
                        if movingPiece.position != -1:
                            board[movingPiece.position] = 0 #clear old position
                        movingPiece.dest = intersections[bestMove[1]].topleft
                        board[bestMove[1]] = movingPiece #set new board position
                        movingPiece.position = bestMove[1]
                        if isMill(bestMove[0].position, 2): #just made a mill
                            removePiece = True
                        else:
                            turn = turn % 2 + 1 #switch turns
                        piecesToPlay = max(0, piecesToPlay - 1)
                if getPiecesRemaining(turn) < 3 or (piecesToPlay <= 1 and getPiecesRemaining(turn) > 3 and not canMove(turn)):
                    stage = 2 #game over

        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                mouseRect = pygame.Rect(pygame.mouse.get_pos(), (1,1))
                if event.button == 1: #left click
                    if stage == 0: #choose # of players
                        if mouseRect.colliderect(pygame.Rect((240, 225), (60, 40))): #1
                            players = 1
                            stage = 1
                        elif mouseRect.colliderect(pygame.Rect((340, 225), (60, 40))): #2
                            players = 2
                            stage = 1
                    elif stage == 1: #in game
                        if turn == 1:
                            if removePiece: #choose a piece to remove
                                if mouseRect.collidelist([i.rect for i in player2Group.sprites()]) != -1: #we're clicking a piece
                                    selectedPiece = player2Group.sprites()[mouseRect.collidelist([i.rect for i in player2Group.sprites()])]
                                    if selectedPiece.position != -1 and (allMills(2) or not isMill(selectedPiece.position, 2)): #every piece is in a mill or selected piece is not in a mill
                                        board[selectedPiece.position] = 0
                                        selectedPiece.remove()
                                        turn = turn % 2 + 1 #switch turns
                                        if getPiecesRemaining(turn) < 3 or (piecesToPlay <= 1 and getPiecesRemaining(turn) > 3 and not canMove(turn)):
                                            stage = 2 #game over
                                        removePiece = False
                                        removedPiece = True
                                    else:
                                        selectedPiece = 0
                            else:
                                if mouseRect.collidelist([i.rect for i in player1Group.sprites()]) != -1: #we're clicking a piece
                                    selectedPiece = player1Group.sprites()[mouseRect.collidelist([i.rect for i in player1Group.sprites()])]
                                    if (piecesToPlay > 0 and selectedPiece.position == -1) or (piecesToPlay == 0 and selectedPiece.position != -1):
                                        selectedPiece.grabbed = True #grab the piece
                                    else:
                                        selectedPiece = 0
                        else:
                            if removePiece: #choose a piece to remove
                                if mouseRect.collidelist([i.rect for i in player1Group.sprites()]) != -1: #we're clicking a piece
                                    selectedPiece = player1Group.sprites()[mouseRect.collidelist([i.rect for i in player1Group.sprites()])]
                                    if selectedPiece.position != -1 and (allMills(1) or not isMill(selectedPiece.position, 1)): #every piece is in a mill or selected piece is not in a mill
                                        board[selectedPiece.position] = 0
                                        selectedPiece.remove()
                                        turn = turn % 2 + 1 #switch turns
                                        removePiece = False
                                        removedPiece = True
                                    else:
                                        selectedPiece = 0
                            else:
                                if mouseRect.collidelist([i.rect for i in player2Group.sprites()]) != -1: #we're clicking a piece
                                    selectedPiece = player2Group.sprites()[mouseRect.collidelist([i.rect for i in player2Group.sprites()])]
                                    if (piecesToPlay > 0 and selectedPiece.position == -1) or (piecesToPlay == 0 and selectedPiece.position != -1):
                                        selectedPiece.grabbed = True #grab the piece
                                    else:
                                        selectedPiece = 0
                    else: #you win, play again?
                        if mouseRect.colliderect(pygame.Rect((240, 225), (60, 40))): #yes
                            stage = 0
                            selectedPiece = 0
                            turn = 1
                            piecesToPlay = 18
                            removePiece = False
                            removedPiece = False
                            allspritesGroup.empty()
                            for i in range(24):
                                board[i] = 0
                            player1Group.empty()
                            for i in range(9):
                                pieces[i] = Piece(1, 160 + (i * 50), 450) #player1
                                pieces[i].add(player1Group)
                            player2Group.empty()
                            for i in range(9):
                                pieces[i + 9] = Piece(2, 160 + (i * 50), 30) #player2
                                pieces[i + 9].add(player2Group)
                        elif mouseRect.colliderect(pygame.Rect((340, 225), (60, 40))): #no
                            return
                    mouseRect = 0
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1: #left click
                    if selectedPiece != 0:
                        if removedPiece == False: #we didn't just remove a piece
                            selectedPiece.grabbed = False
                            targetPosition = selectedPiece.rect.collidelist(intersections)
                            if targetPosition == -1 or board[targetPosition] != 0 or (piecesToPlay == 0 and getPiecesRemaining(turn) > 3 and not isLegalMove(selectedPiece.position, targetPosition)): #we didn't move to an intersection or intersection is full
                                selectedPiece.jumpTo(selectedPiece.xyPrevious) #move the piece back
                            else:
                                if selectedPiece.position != -1:
                                    board[selectedPiece.position] = 0 #clear previous board position
                                board[targetPosition] = selectedPiece #set new board position
                                selectedPiece.position = targetPosition
                                selectedPiece.jumpTo(intersections[targetPosition].topleft) #move the piece
                                selectedPiece.xyPrevious = selectedPiece.xy #reset previous position
                                if isMill(targetPosition, turn): #we have a mill
                                    removePiece = True
                                else:
                                    turn = turn % 2 + 1 #switch turns
                                    if getPiecesRemaining(turn) < 3 or (piecesToPlay <= 1 and getPiecesRemaining(turn) > 3 and not canMove(turn)):
                                        stage = 2 #game over
                                piecesToPlay = max(0, piecesToPlay - 1)
                        else:
                            removedPiece = False
                    mouseRect = 0
                    selectedPiece = 0
            elif event.type == QUIT:
                return

        allspritesGroup.update()
        
        #draw board
        baseSurface.blit(boardImg, (0, 0))
                
        #draw allsprites
        allspritesGroup.draw(baseSurface)

        if stage == 0:
            menuSurface.fill((255, 255, 255))
            if pygame.Rect(pygame.mouse.get_pos(), (1,1)).colliderect(pygame.Rect((240, 225), (60, 40))): #1
                pygame.draw.rect(menuSurface, (180, 180, 180), pygame.Rect((40, 45), (60, 40)), 0)
            elif pygame.Rect(pygame.mouse.get_pos(), (1,1)).colliderect(pygame.Rect((340, 225), (60, 40))): #2
                pygame.draw.rect(menuSurface, (180, 180, 180), pygame.Rect((140, 45), (60, 40)), 0)
            pygame.draw.rect(menuSurface, (10, 10, 10), pygame.Rect((40, 45), (60, 40)), 1)
            pygame.draw.rect(menuSurface, (10, 10, 10), pygame.Rect((140, 45), (60, 40)), 1)
            baseSurface.blit(menuSurface, (200, 180))
            baseSurface.blit(font.render("How many players?", 1, (10, 10, 10)), (205, 190))
            baseSurface.blit(font.render("1", 1, (10, 10, 10)), (265, 235))
            baseSurface.blit(font.render("2", 1, (10, 10, 10)), (365, 235))
        elif stage == 1:
            if removePiece:
                baseSurface.blit(font.render("Choose a piece to remove", 1, (10, 10, 10)), (30, 420))
            #for i in range(24):
            #    baseSurface.blit(font.render(str(getIntersectionValue(2,i)), 1, (10, 10, 10)), intersections[i].topleft)
            baseSurface.blit(font.render(color[turn] + "'s turn", 1, (10, 10, 10)), (30, 400))
        else:
            menuSurface.fill((255, 255, 255))
            if pygame.Rect(pygame.mouse.get_pos(), (1,1)).colliderect(pygame.Rect((240, 225), (60, 40))): #1
                pygame.draw.rect(menuSurface, (180, 180, 180), pygame.Rect((40, 45), (60, 40)), 0)
            elif pygame.Rect(pygame.mouse.get_pos(), (1,1)).colliderect(pygame.Rect((340, 225), (60, 40))): #2
                pygame.draw.rect(menuSurface, (180, 180, 180), pygame.Rect((140, 45), (60, 40)), 0)
            pygame.draw.rect(menuSurface, (10, 10, 10), pygame.Rect((40, 45), (60, 40)), 1)
            pygame.draw.rect(menuSurface, (10, 10, 10), pygame.Rect((140, 45), (60, 40)), 1)
            baseSurface.blit(menuSurface, (200, 180))
            baseSurface.blit(font.render(color[turn % 2 + 1] + " wins!", 1, (10, 10, 10)), (30, 220))
            baseSurface.blit(font.render("Play again?", 1, (10, 10, 10)), (250, 190))
            baseSurface.blit(font.render("YES", 1, (10, 10, 10)), (245, 235))
            baseSurface.blit(font.render("NO", 1, (10, 10, 10)), (355, 235))
        pygame.display.flip()

pygame.init()

if not pygame.font: print 'Warning, fonts disabled'

window = pygame.display.set_mode((640,480)) #initialize window to display
pygame.display.set_caption('Nine Mens Morris')

pygame.mouse.set_visible(1)

baseSurface = pygame.display.get_surface()
menuSurface = pygame.Surface((240, 100))
menuSurface.set_alpha(127)
menuSurface.fill((255, 255, 255))

font = pygame.font.Font(None, 36) #new font object

boardImg = load_image('board.bmp')
boardImg.convert()
boardImg.set_colorkey(0, RLEACCEL)

pieceImg = [0, load_image('blue.bmp', -1), load_image('red.bmp', -1)]
color = [0, 'Blue', 'Red']

board = [0] * 24

allspritesGroup = pygame.sprite.Group()
player1Group = pygame.sprite.Group()
player2Group = pygame.sprite.Group()
selectedGroup = pygame.sprite.Group()

pieces = [0] * 18
for i in range(9):
    pieces[i] = Piece(1, 160 + (i * 50), 450) #player1
    pieces[i].add(player1Group)
for i in range(9):
    pieces[i + 9] = Piece(2, 160 + (i * 50), 30) #player2
    pieces[i + 9].add(player2Group)

#lists of mills that can be made
mills = [[[1, 2], [6, 7]], #0
        [[0, 2], [9, 17]], #1
        [[0, 1], [3, 4]], #2
        [[2, 4], [11, 19]], #3
        [[2, 3], [5, 6]], #4
        [[4, 6], [13, 21]], #5
        [[4, 5], [7, 0]], #6
        [[6, 0], [15, 23]], #7

        [[9, 10], [14, 15]], #8
        [[8, 10], [1, 17]], #9
        [[8, 9], [11, 12]], #10
        [[10, 12], [3, 19]], #11
        [[10, 11], [13, 14]], #12
        [[12, 14], [5, 21]], #13
        [[12, 13], [15, 8]], #14
        [[14, 8], [7, 23]], #15

        [[17, 18], [22, 23]], #16
        [[16, 18], [1, 9]], #17
        [[16, 17], [19, 20]], #18
        [[18, 20], [3, 11]], #19
        [[18, 19], [21, 22]], #20
        [[20, 22], [5, 13]], #21
        [[20, 21], [23, 16]], #22
        [[22, 16], [7, 15]]] #23

neighbors = [[7, 1], #0
             [0, 2, 9], #1
             [1, 3], #2
             [2, 4, 11], #3
             [3, 5], #4
             [4, 6, 13], #5
             [5, 7], #6
             [6, 0, 15], #7

             [15, 9], #8
             [8, 10, 1, 17], #9
             [9, 11], #10
             [10, 12, 3, 19], #11
             [11, 13], #12
             [12, 14, 5, 21], #13
             [13, 15], #14
             [14, 8, 7, 23], #15

             [23, 17], #16
             [16, 18, 9], #17
             [17, 19], #18
             [18, 20, 11], #19
             [19, 21], #20
             [20, 22, 13], #21
             [21, 23], #22
             [22, 16, 15]] #23

#coordinates of intersections
intersections = [pygame.Rect((213, 84), (1, 1)),
                pygame.Rect((364, 84), (1, 1)),
                pygame.Rect((510, 84), (1, 1)),
                pygame.Rect((510, 230), (1, 1)),
                pygame.Rect((510, 381), (1, 1)),
                pygame.Rect((364, 381), (1, 1)),
                pygame.Rect((213, 381), (1, 1)),
                pygame.Rect((213, 230), (1, 1)),

                pygame.Rect((260, 130), (1, 1)),
                pygame.Rect((360, 130), (1, 1)),
                pygame.Rect((460, 130), (1, 1)),
                pygame.Rect((460, 230), (1, 1)),
                pygame.Rect((460, 330), (1, 1)),
                pygame.Rect((360, 330), (1, 1)),
                pygame.Rect((260, 330), (1, 1)),
                pygame.Rect((260, 230), (1, 1)),

                pygame.Rect((313, 181), (1, 1)),
                pygame.Rect((362, 181), (1, 1)),
                pygame.Rect((410, 181), (1, 1)),
                pygame.Rect((410, 230), (1, 1)),
                pygame.Rect((410, 280), (1, 1)),
                pygame.Rect((362, 280), (1, 1)),
                pygame.Rect((313, 280), (1, 1)),
                pygame.Rect((313, 230), (1, 1))]

clock = pygame.time.Clock()
main()
