import unittest

from benchmark.util import RangeList, FAdoize, WeightedRandomItem

class TestFAdoize(unittest.TestCase):
    # Also tested in `test_convert.py` indirectly
    def test_charclass(self):
        f = FAdoize
        self.assertEqual(f('\\d'), '[0-9]')
        self.assertEqual(f('\\D'), '[^0-9]')
        self.assertEqual(f('[\\d]'), '[0-9]')

        self.assertEqual(f('\\s'), ' ')
        self.assertEqual(f('\\S'), '[^ ]')
        self.assertEqual(f('[\\s]'), '[ ]')

        self.assertEqual(f('\\w'), '[0-9A-Za-z_]')
        self.assertEqual(f('\\W'), '[^0-9A-Za-z_]')
        self.assertEqual(f('[\\w]'), '[0-9A-Za-z_]')

    def test_almost_charclass(self):
        f = FAdoize
        self.assertEqual(f('\\\\d'), '(\\ d)')
        self.assertEqual(f('\\\\D'), '(\\ D)')
        self.assertEqual(f('[\\\\d]'), '[\\d]')

        self.assertEqual(f('\\\\s'), '(\\ s)')
        self.assertEqual(f('\\\\S'), '(\\ S)')
        self.assertEqual(f('[\\\\s]'), '[\\s]')

        self.assertEqual(f('\\\\w'), '(\\ w)')
        self.assertEqual(f('\\\\W'), '(\\ W)')
        self.assertEqual(f('[\\\\w]'), '[\\w]')

    def test_forwardslash(self):
        self.assertEqual(FAdoize('//'), '(/ /)')


class TestRangeList(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        inc = lambda x: x+1
        dec = lambda x: x-1
        cls.getRange = lambda _: RangeList([(10, 20), (30, 40), (50, 60), (70, 80), (90, 100)], inc=inc, dec=dec)

    def test_add_base(self):
        l = self.getRange()
        self.assertEqual(str(l), "[(10, 20), (30, 40), (50, 60), (70, 80), (90, 100)]")

    def test_add_noChange(self):
        l = self.getRange()
        l.add(15)
        l.add(90, 91)
        l.add(100)
        self.assertEqual(str(l), "[(10, 20), (30, 40), (50, 60), (70, 80), (90, 100)]")

    def test_add_outsideHigh(self):
        l = self.getRange()
        l.add(200)
        self.assertEqual(str(l), "[(10, 20), (30, 40), (50, 60), (70, 80), (90, 100), (200, 200)]")
        l.add(200, 201)
        self.assertEqual(str(l), "[(10, 20), (30, 40), (50, 60), (70, 80), (90, 100), (200, 201)]")

    def test_add_outsideLow(self):
        l = self.getRange()
        l.add(-200)
        self.assertEqual(str(l), "[(-200, -200), (10, 20), (30, 40), (50, 60), (70, 80), (90, 100)]")
        l.add(-201, -200)
        self.assertEqual(str(l), "[(-201, -200), (10, 20), (30, 40), (50, 60), (70, 80), (90, 100)]")

    def test_add_insideNoOverlap(self):
        l = self.getRange()
        l.add(25)
        l.add(61, 69)
        self.assertEqual(str(l), "[(10, 20), (25, 25), (30, 40), (50, 60), (61, 69), (70, 80), (90, 100)]")

    def test_add_overlapLow(self):
        l = self.getRange()
        l.add(35, 45)
        self.assertEqual(str(l), "[(10, 20), (30, 45), (50, 60), (70, 80), (90, 100)]")

    def test_add_overlapHigh(self):
        l = self.getRange()
        l.add(85, 95)
        self.assertEqual(str(l), "[(10, 20), (30, 40), (50, 60), (70, 80), (85, 100)]")

    def test_add_mergeInternal(self):
        l = self.getRange()
        l.add(20, 61)
        self.assertEqual(str(l), "[(10, 61), (70, 80), (90, 100)]")

    def test_add_mergeUpper(self):
        l = self.getRange()
        l.add(0, 110)
        self.assertEqual(str(l), "[(0, 110)]")

    def test_add_mergeLower(self):
        l = self.getRange()
        l.add(-10, 100)
        self.assertEqual(str(l), "[(-10, 100)]")

    def test_add_mergeAllExact(self):
        l = self.getRange()
        l.add(0, 100)
        self.assertEqual(str(l), "[(0, 100)]")

    def test_add_mergeAllOver(self):
        l = self.getRange()
        l.add(-10, 110)
        self.assertEqual(str(l), "[(-10, 110)]")


    def test_remove_none(self):
        l = self.getRange()
        l.remove(0, 5)
        self.assertEqual(str(l), "[(10, 20), (30, 40), (50, 60), (70, 80), (90, 100)]")
        l.remove(110, 200)
        self.assertEqual(str(l), "[(10, 20), (30, 40), (50, 60), (70, 80), (90, 100)]")
        l.remove(21, 22)
        self.assertEqual(str(l), "[(10, 20), (30, 40), (50, 60), (70, 80), (90, 100)]")

    def test_remove_splitOne(self):
        l = self.getRange()
        l.remove(11, 19)
        self.assertEqual(str(l), "[(10, 10), (20, 20), (30, 40), (50, 60), (70, 80), (90, 100)]")

    def test_remove_one(self):
        l = self.getRange()
        l.remove(10, 20)
        self.assertEqual(str(l), "[(30, 40), (50, 60), (70, 80), (90, 100)]")
        l.remove(90, 100)
        self.assertEqual(str(l), "[(30, 40), (50, 60), (70, 80)]")
        l.remove(50, 60)
        self.assertEqual(str(l), "[(30, 40), (70, 80)]")

    def test_remove_upper(self):
        l = self.getRange()
        l.remove(15, 25)
        self.assertEqual(str(l), "[(10, 14), (30, 40), (50, 60), (70, 80), (90, 100)]")

    def test_remove_lower(self):
        l = self.getRange()
        l.remove(25, 35)
        self.assertEqual(str(l), "[(10, 20), (36, 40), (50, 60), (70, 80), (90, 100)]")

    def test_remove_span(self):
        l = self.getRange()
        l.remove(25, 75)
        self.assertEqual(str(l), "[(10, 20), (76, 80), (90, 100)]")

        l = self.getRange()
        l.remove(15, 65)
        self.assertEqual(str(l), "[(10, 14), (70, 80), (90, 100)]")

    def test_remove_innerOne(self):
        l = self.getRange()
        l.remove(31, 39)
        self.assertEqual(str(l), "[(10, 20), (30, 30), (40, 40), (50, 60), (70, 80), (90, 100)]")

    def test_intersection(self):
        # input cases from the leetcode problem
        a = RangeList([(0,2),(5,10),(13,23),(24,25)], inc=lambda x: x+1, dec=lambda x: x-1)
        b = RangeList([(1,5),(8,12),(15,24),(25,26)], inc=lambda x: x+1, dec=lambda x: x-1)
        self.assertEqual(str(a.intersection(b)), "[(1, 2), (5, 5), (8, 10), (15, 23), (24, 24), (25, 25)]")

        a = RangeList([(1,3), (5,9)], inc=lambda x: x+1, dec=lambda x: x-1)
        b = RangeList([], inc=lambda x: x+1, dec=lambda x: x-1)
        self.assertEqual(str(a.intersection(b)), "[]")

        a = RangeList([], inc=lambda x: x+1, dec=lambda x: x-1)
        b = RangeList([(1,3), (5,9)], inc=lambda x: x+1, dec=lambda x: x-1)
        self.assertEqual(str(a.intersection(b)), "[]")

        a = RangeList([(1, 7)], inc=lambda x: x+1, dec=lambda x: x-1)
        b = RangeList([(3, 10)], inc=lambda x: x+1, dec=lambda x: x-1)
        self.assertEqual(str(a.intersection(b)), "[(3, 7)]")


class TestWeightedRandomItem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samplesize = 15000.0
        cls.iterations = range(int(cls.samplesize))
        cls.threshold = 0.01

    def assertProbabilityClose(self, actual, expected):
        self.assertGreaterEqual(actual, 0)
        self.assertLessEqual(actual, 1)
        self.assertLess(abs(actual - expected), self.threshold)

    def sample(self, rnditem):
        dist = dict()
        for _ in self.iterations:
            item = rnditem.get()
            dist[item] = dist.get(item, 0) + 1
        for item, count in dist.items():
            dist[item] = count / self.samplesize
        return dist


    def test_empty(self):
        rnditem = WeightedRandomItem()
        self.assertIsNone(rnditem.get())

    def test_one(self):
        rnditem = WeightedRandomItem()
        rnditem.add(1, "a")
        self.assertProbabilityClose(self.sample(rnditem)["a"], 1.0)

    def test_two_eq(self):
        rnditem = WeightedRandomItem()
        rnditem.add(1, "a")
        rnditem.add(1, "b")
        self.assertProbabilityClose(self.sample(rnditem)["a"], 0.5)

    def test_two_skew(self):
        rnditem = WeightedRandomItem()
        rnditem.add(1, "a")
        rnditem.add(3, "b")
        self.assertProbabilityClose(self.sample(rnditem)["a"], 0.25)

    def test_many_uniform(self):
        rnditem = WeightedRandomItem()
        rnditem.add(1, "a")
        rnditem.add(1, "b")
        rnditem.add(1, "c")
        rnditem.add(1, "d")
        rnditem.add(1, "e")
        rnditem.add(1, "f")

        distribution = self.sample(rnditem)
        self.assertEqual(len(distribution), 6)
        for prob in distribution.values():
            self.assertProbabilityClose(prob, 1.0/6.0)

    def test_very_skew(self):
        rnditem = WeightedRandomItem()
        rnditem.add(1, "a")
        rnditem.add(1, "b")
        rnditem.add(1, "c")
        rnditem.add(1, "d")
        rnditem.add(96, "x")

        distribution = self.sample(rnditem)
        self.assertProbabilityClose(distribution["x"], 96.0/100.0)
        self.assertProbabilityClose(distribution["a"], 0.01)
        self.assertProbabilityClose(distribution["b"], 0.01)
        self.assertProbabilityClose(distribution["c"], 0.01)
        self.assertProbabilityClose(distribution["d"], 0.01)


if __name__ == "__main__":
    unittest.main()