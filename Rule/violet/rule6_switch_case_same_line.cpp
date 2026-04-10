// 违反规则6：含有switch/case的语句
// 违规形式：case后直接跟语句，未单独缩进
#include <iostream>
using namespace std;

int main()
{
    int x = 2;
    switch(x)
    {
        case 1: cout << 1 << endl; break;
        case 2: cout << 2 << endl; break;
        default: cout << "other" << endl; break;
    }
    return 0;
}
