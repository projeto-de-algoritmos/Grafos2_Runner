import copy
import math
import random
import sys
import threading
import time

import colors
import pygame

size = (1366, 768)
spacing = 80
starting_x = abs((((size[0] - 20) // spacing) * spacing) - size[0]) / 2
starting_y = abs((((size[1] - 20) // spacing) * spacing) - size[1]) / 2
clock = pygame.time.Clock()

rad = math.pi / 180
strong_connected = False
stop_thread = False

pygame.init()

screen = pygame.display.set_mode(size)
screen.fill(colors.WHITE)

pygame.display.set_caption("Runner")
icon = pygame.image.load('images/runners.png')
menu = pygame.image.load('images/menu.png')
icon_big = pygame.transform.scale(icon, (80, 80))
pygame.display.set_icon(icon)

font = pygame.font.SysFont('default', 150)
cost_font = pygame.font.SysFont('default', 30)


# auxiliary function for drawing text
def text_hollow(font, message, font_color):
    not_color = [c ^ 0xFF for c in font_color]
    base = font.render(message, 0, font_color, not_color)
    size = base.get_width() + 2, base.get_height() + 2
    img = pygame.Surface(size, 16)
    img.fill(not_color)
    base.set_colorkey(0)
    img.blit(base, (0, 0))
    img.blit(base, (2, 0))
    img.blit(base, (0, 2))
    img.blit(base, (2, 2))
    base.set_colorkey(0)
    base.set_palette_at(1, not_color)
    img.blit(base, (1, 1))
    img.set_colorkey(not_color)
    return img


# auxiliary function for drawing text
def text_outline(font, message, font_color, outline_color):
    base = font.render(message, 0, font_color)
    outline = text_hollow(font, message, outline_color)
    img = pygame.Surface(outline.get_size(), 16)
    img.blit(base, (1, 1))
    img.blit(outline, (0, 0))
    img.set_colorkey(0)
    return img


def game_win_text():
    win_text = text_outline(font, 'YOU WIN!', colors.WHITE, colors.BLACK)
    screen.blit(win_text, (430, 300))


def game_lose_text():
    win_text = text_outline(font, 'YOU LOSE!', colors.WHITE, colors.BLACK)
    screen.blit(win_text, (410, 300))


def text_objects(text, font):
    text_surface = font.render(text, True, colors.NODE)
    return text_surface, text_surface.get_rect()


# creates a button
def button(msg, x, y, w, h, ic, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(screen, (ic[0] - 20, ic[1] - 20, ic[2] - 20), (x, y, w, h))
        if click[0] == 1 and action is not None:
            action()
    else:
        pygame.draw.rect(screen, ic, (x, y, w, h))

    small_text = pygame.font.SysFont("default", 20)
    text_surf, text_rect = text_objects(msg, small_text)
    text_rect.center = ((x + (w / 2)), (y + (h / 2)))
    screen.blit(text_surf, text_rect)


def menu_game_window():
    menu_game = True

    while menu_game:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

        screen.fill(colors.WHITE)
        screen.blit(menu, (0, 0))

        button('START', 590, 550, 200, 100, colors.BRIGHT_GREEN, game_loop)
        pygame.display.update()
        clock.tick(15)


def restart_game_window():
    restart_game = True

    while restart_game:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

        button('RESTART', 510, 450, 100, 50, colors.GREEN, game_loop)
        button('QUIT', 750, 450, 100, 50, colors.RED, quit_game)

        pygame.display.update()
        clock.tick(15)


def quit_game():
    global stop_thread
    stop_thread = True
    pygame.quit()
    sys.exit()


# stores nodes and positions
class Graph(object):
    def __init__(self):
        self.nodes = set()
        self.positions = dict()

    def add_nodes(self, node, pos):
        self.nodes.add(node)
        self.positions[pos] = node

    def update(self, player, out, machine):
        pygame.draw.rect(screen, colors.BLACK, (50, 3, 104, 20))
        pygame.draw.rect(screen, colors.WHITE, (52, 5, 100, 16))
        pygame.draw.rect(screen, colors.PLAYER, (52, 5, player.stamina * 10, 16))
        pygame.draw.rect(screen, colors.BLACK, (1230, 3, 104, 20))
        pygame.draw.rect(screen, colors.WHITE, (1232, 5, 100, 16))
        pygame.draw.rect(screen, colors.MACHINE, (1232, 5, machine.stamina * 10, 16))
        for node in self.nodes:
            if player.position == (node.rect[0], node.rect[1]):
                draw_circle(node, colors.PLAYER)
            elif machine.position == (node.rect[0], node.rect[1]):
                draw_circle(node, colors.MACHINE)
            elif out.position == (node.rect[0], node.rect[1]):
                draw_circle(node, colors.EXIT)
            elif node.buff:
                draw_circle(node, colors.BUFF)
            else:
                draw_circle(node, colors.NODE)


class Node(object):
    def __init__(self):
        self.rect = None
        self.color = colors.NODE
        self.neighbours = set()
        self.strong = False
        self.buff = False


class Player(object):
    def __init__(self):
        self.color = None
        self.position = random_pos()
        self.stamina = 10


class Exit(object):
    def __init__(self):
        self.color = colors.EXIT
        self.position = random_pos()


def dijkstra(graph, start, goal):
    unseen_nodes = dict.fromkeys(graph.nodes, 0)
    shortest_distance = {}
    predecessor = {}
    path = []
    infinity = 9999999

    for node in unseen_nodes:
        shortest_distance[node] = infinity
    shortest_distance[start] = 0

    while unseen_nodes:
        min_node = None
        for node in unseen_nodes:
            if min_node is None:
                min_node = node
            elif shortest_distance[node] < shortest_distance[min_node]:
                min_node = node

        for neighbour, weight in min_node.neighbours.items():
            if weight + shortest_distance[min_node] < shortest_distance[neighbour]:
                shortest_distance[neighbour] = weight + shortest_distance[min_node]
                predecessor[neighbour] = min_node
        unseen_nodes.pop(min_node)

    current_node = goal
    while current_node != start:
        path.insert(0, current_node)
        current_node = predecessor[current_node]

    return path, shortest_distance[goal]


# generate stamina nodes for the player
def create_buff(graph, player, machine, out):
    for i in range(1, 6):
        x = random.randint(0, 16) * 80 + starting_x
        y = random.randint(0, 9) * 80 + starting_y
        while (x, y) == player.position or (x, y) == machine.position or (x, y) == out.position or graph.positions[(x, y)].buff:
            x = random.randint(0, 16) * 80 + starting_x
            y = random.randint(0, 9) * 80 + starting_y
        else:
            graph.positions[(x, y)].buff = True


# generates graph with random edges
def create_graph():
    pos = [starting_x, starting_y]
    graph = Graph()
    nodes = []
    while pos[1] <= size[1] - starting_y:
        node = Node()
        graph.add_nodes(node, (pos[0], pos[1]))
        nodes.append(node)
        node.rect = pygame.Rect(pos[0], pos[1], 20, 20)
        if pos[0] == size[0] - starting_x:
            pos[0] = starting_x
            pos[1] += spacing
            continue
        pos[0] += spacing

    pos = [starting_x, starting_y]
    for node in nodes:
        if pos[1] > size[1] - starting_y:
            break
        if pos[0] > size[0] - starting_x:
            pos[0] = starting_x
            pos[1] += spacing

        if pos[0] - spacing > 0:
            if random.randint(0, 1):
                neighbour = graph.positions[pos[0] - spacing, pos[1]]
                node.neighbours.add(neighbour)
        if pos[0] + spacing < size[0]:
            if random.randint(0, 1):
                neighbour = graph.positions[pos[0] + spacing, pos[1]]
                node.neighbours.add(neighbour)
        if pos[1] - spacing > 0:
            if random.randint(0, 1):
                neighbour = graph.positions[pos[0], pos[1] - spacing]
                node.neighbours.add(neighbour)
        if pos[1] + spacing < size[1]:
            if random.randint(0, 1):
                neighbour = graph.positions[pos[0], pos[1] + spacing]
                node.neighbours.add(neighbour)

        pos[0] += spacing

    return graph


# main function to ensure strong connectivity
def strongly_connect(graph, rev_graph, start_pos):
    global strong_connected

    bfs(graph.positions[start_pos])
    bfs(rev_graph.positions[start_pos])

    update_strong_component(graph, rev_graph)

    for node in graph.nodes:
        if not node.strong:
            strong_connected = False
            break
        strong_connected = True

    if strong_connected:
        return

    fix_connectivity(graph, rev_graph)

    for node in graph.nodes:
        node.strong = False
        rev_graph.positions[node.rect[0], node.rect[1]].strong = False

    strongly_connect(graph, rev_graph, start_pos)


# reverse all edges of given graph
def reverse_graph(graph):
    rev_graph = copy.deepcopy(graph)
    for node in rev_graph.nodes:
        node.neighbours.clear()
    for node in graph.nodes:
        for neighbour in node.neighbours:
            rev_graph.positions[neighbour.rect[0], neighbour.rect[1]].neighbours.add(rev_graph.positions[node.rect[0],
                                                                                                         node.rect[1]])
    return rev_graph


# update nodes marked as strongly connected
def update_strong_component(graph, rev_graph):
    for node in graph.nodes:
        if node.strong and rev_graph.positions[node.rect[0], node.rect[1]].strong:
            continue
        else:
            node.strong = False


# fixes connectivity by generating edges between strongly connected component and other nodes
def fix_connectivity(graph, rev_graph):
    for node in graph.nodes:
        if not node.strong:
            if node.rect[0] - spacing > 0:
                if graph.positions[node.rect[0] - spacing, node.rect[1]].strong:
                    node.neighbours.add(graph.positions[node.rect[0] - spacing, node.rect[1]])
                    graph.positions[node.rect[0] - spacing, node.rect[1]].neighbours.add(node)
                    rev_graph.positions[node.rect[0], node.rect[1]].neighbours.add(
                        rev_graph.positions[node.rect[0] - spacing, node.rect[1]])
                    rev_graph.positions[node.rect[0] - spacing, node.rect[1]].neighbours.add(
                        rev_graph.positions[node.rect[0], node.rect[1]])
                    return
            if node.rect[0] + spacing < size[0]:
                if graph.positions[node.rect[0] + spacing, node.rect[1]].strong:
                    node.neighbours.add(graph.positions[node.rect[0] + spacing, node.rect[1]])
                    graph.positions[node.rect[0] + spacing, node.rect[1]].neighbours.add(node)
                    rev_graph.positions[node.rect[0], node.rect[1]].neighbours.add(
                        rev_graph.positions[node.rect[0] + spacing, node.rect[1]])
                    rev_graph.positions[node.rect[0] + spacing, node.rect[1]].neighbours.add(
                        rev_graph.positions[node.rect[0], node.rect[1]])
                    return
            if node.rect[1] - spacing > 0:
                if graph.positions[node.rect[0], node.rect[1] - spacing].strong:
                    node.neighbours.add(graph.positions[node.rect[0], node.rect[1] - spacing])
                    graph.positions[node.rect[0], node.rect[1] - spacing].neighbours.add(node)
                    rev_graph.positions[node.rect[0], node.rect[1]].neighbours.add(
                        rev_graph.positions[node.rect[0], node.rect[1] - spacing])
                    rev_graph.positions[node.rect[0], node.rect[1] - spacing].neighbours.add(
                        rev_graph.positions[node.rect[0], node.rect[1]])
                    return
            if node.rect[1] + spacing < size[1]:
                if graph.positions[node.rect[0], node.rect[1] + spacing].strong:
                    node.neighbours.add(graph.positions[node.rect[0], node.rect[1] + spacing])
                    graph.positions[node.rect[0], node.rect[1] + spacing].neighbours.add(node)
                    rev_graph.positions[node.rect[0], node.rect[1]].neighbours.add(
                        rev_graph.positions[node.rect[0], node.rect[1] + spacing])
                    rev_graph.positions[node.rect[0], node.rect[1] + spacing].neighbours.add(
                        rev_graph.positions[node.rect[0], node.rect[1]])
                    return


def bfs(node):
    node.strong = True
    queue = [node]

    while queue:
        s = queue.pop(0)

        for neighbour in s.neighbours:
            if not neighbour.strong:
                neighbour.strong = True
                queue.append(neighbour)


def draw_edges(graph):
    for node in graph.nodes:
        for neighbour in node.neighbours:
            if node.rect[0] > neighbour.rect[0]:
                arrow(screen, colors.NODE, colors.NODE, node.rect.center, (neighbour.rect.center[0] + 15,
                                                                           neighbour.rect.center[1]), 5)
                if node in neighbour.neighbours:
                    neighbour.neighbours[node] = node.neighbours[neighbour]
                text = text_outline(cost_font, str(node.neighbours[neighbour]), colors.BLACK, colors.WHITE)
                screen.blit(text, (node.rect[0] - 35, node.rect[1]))
            elif node.rect[0] < neighbour.rect[0]:
                arrow(screen, colors.NODE, colors.NODE, node.rect.center, (neighbour.rect.center[0] - 15,
                                                                           neighbour.rect.center[1]), 5)
                if node in neighbour.neighbours:
                    neighbour.neighbours[node] = node.neighbours[neighbour]
                    continue
                text = text_outline(cost_font, str(node.neighbours[neighbour]), colors.BLACK, colors.WHITE)
                screen.blit(text, (node.rect[0] + 40, node.rect[1]))
            elif node.rect[1] < neighbour.rect[1]:
                arrow(screen, colors.NODE, colors.NODE, node.rect.center, (neighbour.rect.center[0],
                                                                           neighbour.rect.center[1] - 15), 5)
                if node in neighbour.neighbours:
                    neighbour.neighbours[node] = node.neighbours[neighbour]
                text = text_outline(cost_font, str(node.neighbours[neighbour]), colors.BLACK, colors.WHITE)
                screen.blit(text, (node.rect[0] + 4, node.rect[1] + 40))
            elif node.rect[1] > neighbour.rect[1]:
                arrow(screen, colors.NODE, colors.NODE, node.rect.center, (neighbour.rect.center[0],
                                                                           neighbour.rect.center[1] + 15), 5)
                if node in neighbour.neighbours:
                    neighbour.neighbours[node] = node.neighbours[neighbour]
                    continue
                text = text_outline(cost_font, str(node.neighbours[neighbour]), colors.BLACK, colors.WHITE)
                screen.blit(text, (node.rect[0] + 4, node.rect[1] - 35))


# returns random position
def random_pos():
    return (random.randrange(starting_x, (((size[0] - 20) // spacing) * spacing), spacing),
            random.randrange(starting_y, (((size[1] - 20) // spacing) * spacing), spacing))


def draw_circle(node, color):
    return pygame.draw.circle(screen, color, node.rect.center, 10)


# function to transform line to line with arrow
def arrow(scr, lcolor, tricolor, start, end, trirad, thickness=1):
    pygame.draw.line(scr, lcolor, start, end, thickness)
    rotation = (math.atan2(start[1] - end[1], end[0] - start[0])) + math.pi / 2
    pygame.draw.polygon(scr, tricolor, ((end[0] + trirad * math.sin(rotation),
                                         end[1] + trirad * math.cos(rotation)),
                                        (end[0] + trirad * math.sin(rotation - 120 * rad),
                                         end[1] + trirad * math.cos(rotation - 120 * rad)),
                                        (end[0] + trirad * math.sin(rotation + 120 * rad),
                                         end[1] + trirad * math.cos(rotation + 120 * rad))))


# ensures minimum distance between starting nodes
def min_dist(graph, player, machine, out):
    player_distance = dijkstra(graph, graph.positions[player.position], graph.positions[out.position])
    while player_distance[1] < 20:
        player.position = random_pos()
        player_distance = dijkstra(graph, graph.positions[player.position], graph.positions[out.position])

    machine_distance = dijkstra(graph, graph.positions[machine.position], graph.positions[out.position])
    while machine_distance[1] <= player_distance[1]:
        machine.position = random_pos()
        machine_distance = dijkstra(graph, graph.positions[machine.position], graph.positions[out.position])

    return machine_distance


def machine_mov(machine, path, player, graph):
    global stop_thread
    current_node = graph.positions[machine.position]
    for pos in path[0]:
        if stop_thread:
            break
        time.sleep(1)
        if player.stamina < 10:
            player.stamina += 1
        if machine.stamina < 10:
            machine.stamina += 1
        while machine.stamina < current_node.neighbours[pos]:
            time.sleep(1)
            if player.stamina < 10:
                player.stamina += 1
            if machine.stamina < 10:
                machine.stamina += 1
        time.sleep(0.25)
        machine.stamina -= current_node.neighbours[pos]
        machine.position = (pos.rect[0], pos.rect[1])
        current_node = graph.positions[machine.position]
        if current_node.buff:
            machine.stamina = 10
            current_node.buff = False


# main game loop where player input is read
def game_loop():
    screen.fill(colors.WHITE)
    graph = create_graph()
    player = Player()
    player.color = colors.PLAYER
    machine = Player()
    machine.color = colors.MACHINE
    out = Exit()
    out.position = random_pos()

    rev_graph = reverse_graph(graph)
    strongly_connect(graph, rev_graph, player.position)

    for node in graph.nodes:
        node.neighbours = dict.fromkeys(node.neighbours, random.randint(1, 3))

    draw_edges(graph)

    path = min_dist(graph, player, machine, out)

    global stop_thread
    stop_thread = False

    x = threading.Thread(target=machine_mov, args=(machine, path, player, graph))
    x.start()

    create_buff(graph, player, machine, out)

    while True:

        graph.update(player, out, machine)

        if player.position == out.position:
            game_win_text()
            restart_game_window()
            quit_game()
        elif machine.position == out.position:
            game_lose_text()
            restart_game_window()
            quit_game()
        elif graph.positions[player.position].buff:
            player.stamina = 10
            graph.positions[player.position].buff = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if event.type == pygame.KEYDOWN:
                (x, y) = player.position
                if event.key == pygame.K_UP:
                    if (x, y - spacing) in graph.positions:
                        if graph.positions[x, y - spacing] in graph.positions[x, y].neighbours:
                            player_node = graph.positions[x, y]
                            player_node_neighbour = graph.positions[x, y - spacing]
                            if player.stamina < player_node.neighbours[player_node_neighbour]:
                                continue
                            else:
                                player.stamina -= player_node.neighbours[player_node_neighbour]
                                player.position = x, y - spacing
                elif event.key == pygame.K_DOWN:
                    if (x, y + spacing) in graph.positions:
                        if graph.positions[x, y + spacing] in graph.positions[x, y].neighbours:
                            player_node = graph.positions[x, y]
                            player_node_neighbour = graph.positions[x, y + spacing]
                            if player.stamina < player_node.neighbours[player_node_neighbour]:
                                continue
                            else:
                                player.stamina -= player_node.neighbours[player_node_neighbour]
                                player.position = x, y + spacing
                elif event.key == pygame.K_LEFT:
                    if (x - spacing, y) in graph.positions:
                        if graph.positions[x - spacing, y] in graph.positions[x, y].neighbours:
                            player_node = graph.positions[x, y]
                            player_node_neighbour = graph.positions[x - spacing, y]
                            if player.stamina < player_node.neighbours[player_node_neighbour]:
                                continue
                            else:
                                player.stamina -= player_node.neighbours[player_node_neighbour]
                                player.position = x - spacing, y
                elif event.key == pygame.K_RIGHT:
                    if (x + spacing, y) in graph.positions:
                        if graph.positions[x + spacing, y] in graph.positions[x, y].neighbours:
                            player_node = graph.positions[x, y]
                            player_node_neighbour = graph.positions[x + spacing, y]
                            if player.stamina < player_node.neighbours[player_node_neighbour]:
                                continue
                            else:
                                player.stamina -= player_node.neighbours[player_node_neighbour]
                                player.position = x + spacing, y

        pygame.display.update()
        clock.tick(60)


def main():
    menu_game_window()
    game_loop()


if __name__ == "__main__":
    main()
