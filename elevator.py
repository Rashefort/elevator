# tested on Win 7 32 bit, python 3.6.3
# -*- coding: utf-8 -*-
from threading import Thread
import asyncio
import curses
import math
import sys


KEYS = '123456789ABCDEFGHIJK'
EXIT = '\x1b' # hex(27)


#------------------------------------------------------------------------------
def press():
    while True:
        key = str(house.getkey()).upper()

        if key != EXIT:
            floor = KEYS.find(key[-1]) + 1

            if key[-1] in KEYS and 0 < floor <= floors:
                loop.call_soon_threadsafe(queue.put_nowait, floor)
                window = house if len(key) == 1 else lift
                window.addstr(floor, 0, f' {key[-1]} ', curses.color_pair(2))
                window.refresh()

        else:
            loop.call_soon_threadsafe(queue.put_nowait, EXIT)
            break

#------------------------------------------------------------------------------
async def check(calls, semaphore):
    while True:
        floor = await queue.get()

        if floor != EXIT:
            if floor not in calls:
                calls.append(floor)
                semaphore.release()
        else:
            task_elevator.cancel()
            break

#------------------------------------------------------------------------------
async def elevator(calls, semaphore):
    here = 1    # этаж на котором находится лифт;
    there = 1   # этаж на который следует лифт;

    messages.addstr(f'lift on the {here} floor\n')
    messages.refresh()

    while True:
        await semaphore.acquire()
        there = calls.pop(0)

        while here != there:
            await asyncio.sleep(hight / speed)

            house.addstr(here, 0, f' {KEYS[here-1]} ', curses.color_pair(1))
            lift.addstr(here, 0, f' {KEYS[here-1]} ', curses.color_pair(1))

            here += int(math.copysign(1, there - here))

            house.addstr(here, 0, f' {KEYS[here-1]} ', curses.color_pair(4))
            house.refresh()

            lift.addstr(here, 0, f' {KEYS[here-1]} ', curses.color_pair(4))
            lift.refresh()

            messages.addstr(f'lift on the {here} floor\n')
            messages.refresh()

            # проверка, был ли вызван лифт с текущего этажа;
            if here in calls:
                calls.insert(0, there)
                there = calls.pop(calls.index(here))
                semaphore.acquire()

        if here == there:
            house.addstr(here, 0, f'[{KEYS[here-1]}]', curses.color_pair(5))
            house.refresh()

            lift.addstr(here, 0, f'[{KEYS[here-1]}]', curses.color_pair(5))
            lift.refresh()

            messages.addstr('the doors opened\n')
            messages.refresh()

            await asyncio.sleep(time)

            house.addstr(here, 0, f' {KEYS[here-1]} ', curses.color_pair(4))
            house.refresh()

            lift.addstr(here, 0, f' {KEYS[here-1]} ', curses.color_pair(4))
            lift.refresh()

            messages.addstr('the doors closed\n')
            messages.refresh()


#------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        if len(sys.argv) == 5 and 5 <= int(sys.argv[1]) <=20:
            floors, hight, speed, time = list(map(int, sys.argv[1:]))
        else:
            raise ValueError

    except ValueError:
        floors, hight, speed, time = 20, 3, 2, 2

    #--------------------------------------------------------------------------
    stdscr = curses.initscr()
    size = stdscr.getmaxyx()

    curses.curs_set(False)
    curses.noecho()

    curses.start_color()
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_RED)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_WHITE)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)

    stdscr.addstr(0, 9, f'press button [1-{KEYS[floors-1]}]')
    stdscr.addstr(0, 28, f'or ALT+[1-{KEYS[floors-1]}]\n')
    stdscr.addstr(0, size[1] - 19, ' press Esc to exit ', curses.color_pair(3))
    stdscr.refresh()

    house = stdscr.subwin(size[0], 4, 0, 0)
    house.border(' ', '|', ' ', ' ', ' ', '|', ' ', '|')
    house.keypad(True)

    lift = stdscr.subwin(size[0], 4, 0, 4)
    lift.border(' ', '|', ' ', ' ', ' ', '|', ' ', '|')
    lift.keypad(True)

    house.addstr(1, 0, ' 1 ', curses.color_pair(4))
    lift.addstr(1, 0, ' 1 ', curses.color_pair(4))
    for i in range(2, floors + 1):
        char = chr(i + (48 if i < 10 else 55))
        house.addstr(i, 1, char, curses.color_pair(1))
        lift.addstr(i, 1, char, curses.color_pair(1))

    house.refresh()
    lift.refresh()

    messages = stdscr.subwin(size[0] - 1, size[1] - 10, 1, 10)
    messages.scrollok(True)

    #--------------------------------------------------------------------------
    loop = asyncio.get_event_loop()
    semaphore = asyncio.Semaphore(value=0, loop=loop)
    queue = asyncio.Queue(loop=loop)
    calls = list()

    Thread(target=press).start()

    task_elevator = loop.create_task(elevator(calls, semaphore))
    task_check = loop.create_task(check(calls, semaphore))

    try:
        loop.run_until_complete(asyncio.wait([task_elevator, task_check]))
    finally:
        loop.close()

    curses.endwin()
