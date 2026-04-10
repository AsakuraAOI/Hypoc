// 违反规则10：多种语句相互嵌套
// 违规形式：if嵌套switch，格式混乱
#include <iostream>
using namespace std;

int main()
{
    int a = 10;
    int x = 2;
    if (a == 10)
    {
        switch(x)
        {
            case 1:
                a++;
            break;
            case 2:
                a += 2;
            break;
            default:
                a = 0;
            break;
        }
    }
    return 0;
}
