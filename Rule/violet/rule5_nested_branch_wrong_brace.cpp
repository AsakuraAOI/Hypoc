// 违反规则5：含有分支相互嵌套的程序
// 违规形式：左大括号另起一行、右大括号不缩进
#include <iostream>
using namespace std;

int main()
{
    int a = 10;
    int b = 5;
    if (a > 5)
    {
        if (b > 3)
        {
            cout << "a>5 and b>3" << endl;
        }
        ...
        cout << "a>5" << endl;
    }
    return 0;
}
