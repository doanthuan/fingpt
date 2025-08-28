# In a string composed of 'L', 'R', and 'X' characters, like "RXXLRXRXL", a move consists of either replacing one occurrence of "XL" with "LX", or replacing one occurrence of "RX" with "XR". Given the starting string start and the ending string result, return True if and only if there exists a sequence of moves to transform start to result.

 

# Example 1:

# Input: start = "RXXLRXRXL", result = "XRLXXRRLX"
# Output: true
# Explanation: We can transform start to result following these steps:
# RXXLRXRXL ->
# XRXLRXRXL ->
# XRLXRXRXL ->
# XRLXXRRXL ->
# XRLXXRRLX
# Example 2:

# Input: start = "X", result = "L"
# Output: false
 

# Constraints:

# 1 <= start.length <= 104
# start.length == result.length
# Both start and result will only consist of characters in 'L', 'R', and 'X'.
import copy
cache_rs = dict()
def is_transform(input, output):
    if input in cache_rs.keys():
        return cache_rs[input]
    
    # print("checking:", input)
    if input == output:
        cache_rs[input] = True
        return True
    
    # scan input, find candidates
    ls_input = list(input)
    c = copy.deepcopy(ls_input)
    for i in range(len(ls_input) - 1):
        if ls_input[i] == "X" and ls_input[i+1] == "L":
            c[i] = "L"
            c[i+1] = "X"
            if is_transform("".join(c), output):
                cache_rs["".join(c)] = True
                return True
            
        if ls_input[i] == "R" and ls_input[i+1] == "X":
            c[i] = "X"
            c[i+1] = "R"
            if is_transform("".join(c), output):
                cache_rs["".join(c)] = True
                return True
    
    cache_rs[input] = False
    return False
        
    
print("case 1:", is_transform("RXXLRXRXL", "XRLXXRRLX"))

print("case 2:", is_transform("X", "L"))

print("case 3:", is_transform("LXXLXRLXXL", "XLLXRXLXLX"))

print("case 4:", is_transform("RXR", "XXR"))

