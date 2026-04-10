// 违反规则7：含有循环结构的程序（while和for）
// 违规形式：单语句循环与关键字同行，空语句分号同行
#include <iostream>
using namespace std;

int main()
{
    int a = 0;
    while (a < 10) a++; // 单语句与while同行
    for (int i = 0; i < 5; i++) cout << i << endl; // 单语句与for同行
    while (a < 20); // 空语句分号同行
    return 0;
}
