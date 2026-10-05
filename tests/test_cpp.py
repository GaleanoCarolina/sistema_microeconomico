from services.cpp_service import CPPService
from utils.money import to_cents

def test_cpp_first_purchase():
    assert CPPService.calculate(0,0,10,to_cents('10')) == to_cents('10')

def test_cpp_second_higher_cost():
    assert CPPService.calculate(10,to_cents('10'),20,to_cents('12')) == to_cents('11.33')

def test_cpp_lower_cost():
    assert CPPService.calculate(10,to_cents('12'),10,to_cents('10')) == to_cents('11')

def test_cpp_zero_inventory():
    assert CPPService.calculate(0,to_cents('99'),5,to_cents('7.25')) == to_cents('7.25')
