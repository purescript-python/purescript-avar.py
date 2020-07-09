import threading


class EMPTY:
    pass


class MutableQueue:
    def __init__(self):
        self.head = None
        self.last = None
        self.size = 0


class MutableCell:
    def __init__(self, queue, value):
        self.queue = queue
        self.value = value
        self.next = None
        self.prev = None


class AVar:
    def __init__(self, value):
        self.draining = False
        self.error = None
        self.value = value
        self.takes = MutableQueue()
        self.reads = MutableQueue()
        self.puts = MutableQueue()


class ____:
    @staticmethod
    def runEff(eff):
        try:
            eff()
        except Exception as e:

            def _throw():
                raise e

            t = threading.Thread(target=_throw)
            t.start()

    @staticmethod
    def putLast(queue, value):
        cell = MutableCell(queue, value)
        if queue.size == 0:
            queue.head = cell
        elif queue.size == 1:
            cell.prev = queue.head
            queue.head.next = cell
            queue.last = cell

        else:
            cell.prev = queue.last
            queue.last.next = cell
            queue.last = cell

        queue.size += 1
        return cell

    @staticmethod
    def takeLast(queue):
        cell = None
        if queue.size == 0:
            return None
        if queue.size == 1:
            cell = queue.head
            queue.head = None
        elif queue.size == 2:
            cell = queue.last
            queue.head.next = None
            queue.last = None
        else:
            cell = queue.last
            queue.last = cell.prev
            queue.last.next = None
        cell.prev = None
        cell.queue = None
        queue.size -= 1
        return cell.value

    @staticmethod
    def takeHead(queue):
        cell = None
        if queue.size == 0:
            return None
        if queue.size == 1:
            cell = queue.head
            queue.head = None
        elif queue.size == 2:
            cell = queue.head
            queue.last.prev = None
            queue.head = queue.last
            queue.last = None
        else:
            cell = queue.head
            queue.head = cell.next
            queue.head.prev = None
        cell.next = None
        cell.queue = None
        queue.size -= 1
        return cell.value

    @staticmethod
    def deleteCell(cell):
        if cell.queue == None:
            return None
        if cell.queue.last == cell:
            ____.takeLast(cell.queue)
            return None
        if cell.queue.head == cell:
            ____.takeHead(cell.queue)
            return None
        if cell.prev:
            cell.prev.next = cell.next
        if cell.next:
            cell.next.prev = cell.prev
        cell.queue.size -= 1
        cell.queue = None
        cell.value = None
        cell.next = None
        cell.prev = None

    @staticmethod
    def drainVar(util, avar):
        if avar.draining:
            return None
        ps = avar.puts
        ts = avar.takes
        rs = avar.reads
        p = None
        r = None
        t = None
        value = None
        rsize = None
        avar.draining = True
        while True:
            p = None
            r = None
            t = None
            value = avar.value
            rsize = rs.size
            if avar.error is not None:
                value = util["left"](avar.error)
                while True:
                    p = ____.takeHead(ps)
                    if p is None:
                        break
                    ____.runEff(p.cb(value))
                while True:
                    r = ____.takeHead(rs)
                    if r is None:
                        break
                    ____.runEff(r(value))
                while True:
                    t = ____.takeHead(ts)
                    if t is None:
                        break
                    ____.runEff(t(value))
                break
            if value == EMPTY:
                p = ____.takeHead(ps)
                if p:
                    avar.value = p.value
                    value = p.value
            if value != EMPTY:
                t = ____.takeHead(ts)
                while rsize > 0:
                    rsize -= 1
                    r = ____.takeHead(rs)
                    if not r:
                        break
                    ____.runEff(r(util["right"](value)))
                if t is not None:
                    avar.value = EMPTY
                    ____.runEff(t(util["right"](value)))
            if p is not None:
                ____.runEff(p.cb(util["right"](None)))
            if ((avar.value == EMPTY) and (ps.size == 0)) or (
                (avar.value != EMPTY) and (ts.size == 0)
            ):
                break
        avar.draining = False


def empty():
    return AVar(EMPTY)


def _newVar(value):
    def _newVar1():
        return AVar(value)

    return _newVar1


def _killVar(util, error, avar):
    def _killVar1():
        if avar.error == None:
            avar.error = error
            avar.value = EMPTY
            ____.drainVar(util, avar)

    return _killVar1


class Puttable:
    def __init__(self, cb, value):
        self.cb = cb
        self.value = value


def _putVar(util, value, avar, cb):
    def _putVar1():
        cell = ____.putLast(avar.puts, Puttable(cb, value))
        ____.drainVar(util, avar)

        def _putVar2():
            ____.deleteCell(cell)

        return _putVar2

    return _putVar1


def _takeVar(util, avar, cb):
    def _takeVar1():
        cell = ____.putLast(avar.takes, cb)
        ____.drainVar(util, avar)

        def _takeVar2():
            ____.deleteCell(cell)

        return _takeVar2

    return _takeVar1


def _readVar(util, avar, cb):
    def _readVar1():
        cell = ____.putLast(avar.reads, cb)
        ____.drainVar(util, avar)

        def _readVar2():
            ____.deleteCell(cell)

        return _readVar2

    return _readVar1


def _tryPutVar(util, value, avar):
    def _tryPutVar1():
        if (avar.value == EMPTY) and (avar.error == None):
            avar.value = value
            ____.drainVar(util, avar)
            return True
        else:
            return False

    return _tryPutVar1


def _tryTakeVar(util, avar):
    def _tryTakeVar1():
        value = avar.value
        if value == EMPTY:
            return util["nothing"]
        else:
            avar.value = EMPTY
            ____.drainVar(util, avar)
            return util["just"](value)

    return _tryTakeVar1


def _tryReadVar(util, avar):
    def _tryReadVar1():
        if avar.value == EMPTY:
            return util["nothing"]
        else:
            return util["just"](avar.value)

    return _tryReadVar1


def _status(util, avar):
    def _status1():
        if avar.error:
            return util["killed"](avar.error)

        if avar.value == EMPTY:
            return util["empty"]

        return util["filled"](avar.value)

    return _status1

