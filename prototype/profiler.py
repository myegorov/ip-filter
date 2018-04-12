from functools import wraps

def count_invocations(func):
    '''Count the number of times `func` was called.
    '''
    @wraps(func)
    def register(*args, **kwargs):
        register.ncalls += 1
        return func(*args, **kwargs)
    register.ncalls = 0
    return register

if __name__ == "__main__":
    @count_invocations
    def plus1(num):
        return num+1

    x = 0
    for i in range(10):
        x+=plus1(i)

    print(plus1.ncalls) # => 10

