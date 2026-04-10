// 违反规则4：含有多分支结构的程序
// 违规形式：if-elseif-else单语句同行
#include <iostream>
using namespace std;

int main()
{
    int score = 85;
    if (score >= 90) cout << "A" << endl;
    else if (score >= 80) cout << "B" << endl;
    else cout << "C" << endl;
    return 0;
}
