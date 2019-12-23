def rev_alpha_numeric(input_string):
    #on to you now
    res = ""
    rev = input_string[::-1]
    s_indx = 0
    for indx in range(0,len(input_string)):
        if not input_string[indx].isalnum():
            res = res+input_string[indx]
        else:
            if rev[s_indx].isalnum():
                res = res+rev[s_indx]
                s_indx+=1
            else:
                for ss in range(s_indx, len(input_string)):
                    s_indx+=1
                    if rev[ss].isalnum():
                        res = res+rev[ss]
                        break
    return res

if __name__ == '__main__':
    input_string = raw_input()
    result = rev_alpha_numeric(input_string)
    print(result)
