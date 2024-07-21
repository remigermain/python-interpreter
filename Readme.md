Python3.12 bytescodes interpreter writed in python3.12 [see dis](https://docs.python.org/3/library/dis.html)

## Working:
- function definition
- iterable
- generator ( yield )
- for-loop / else
- while / else
- if / elif / else
- return
- f'string
- call function
- call attr
- all operators
- all compares
- variables scope
- comprehension list/dict/set
- unpack sequence

## Not working:
- class definition
- super() in class
- async
- try / except / else / finally / raise
- context manager (`__exit__` not work)
- default args/kwargs on functions (partial)
- comprehension tuple

### Usage
```
python3.12 interpreter.py tests.py
python3.12 interpreter.py tests.py --debug
python3.12 interpreter.py --help
```

### Instructions
Cpython Instructions working:
> - POP_TOP
> - COPY
> - NOP
> - RESUME
> - PUSH_NULL
> - FORMAT_VALUE
> - RETURN_VALUE
> - RETURN_CONST
> - STORE_FAST
> - STORE_GLOBAL
> - STORE_NAME
> - STORE_SUBSCR
> - STORE_SLICE
> - LOAD_CONST
> - LOAD_FAST_AND_CLEAR
> - LOAD_FAST
> - LOAD_GLOBAL
> - LOAD_NAME
> - LOAD_FROM_DICT_OR_GLOBALS
> - LOAD_ATTR
> - MAKE_FUNCTION
> - CALL
> - KW_NAMES
> - POP_JUMP_IF_TRUE
> - POP_JUMP_IF_FALSE
> - POP_JUMP_IF_NOT_NONE
> - POP_JUMP_IF_NONE
> - JUMP_FORWARD
> - JUMP_BACKWARD
> - BUILD_STRING
> - BUILD_MAP
> - MAP_ADD
> - DICT_MERGE
> - DICT_UPDATE
> - BUILD_TUPLE
> - BUILD_LIST
> - LIST_APPEND
> - LIST_EXTEND
> - BUILD_SET
> - SET_ADD
> - SET_UPDATE
> - SWAP
> - UNPACK_SEQUENCE
> - IS_OP
> - CONTAINS_OP
> - COMPARE_OP
> - BINARY_OP
> - UNARY_NOT
> - UNARY_NEGATIVE
> - UNARY_INVERT
> - GET_LEN
> - BINARY_SUBSCR
> - BINARY_SLICE
> - DELETE_SUBSCR
> - DELETE_NAME
> - DELETE_GLOBAL
> - DELETE_FAST
> - GET_ITER
> - FOR_ITER
> - END_FOR
> - RETURN_GENERATOR
> - GET_YIELD_FROM_ITER
> - YIELD_VALUE
> - IMPORT_NAME
> - IMPORT_FROM
> - BEFORE_WITH
> - WITH_EXCEPT_START