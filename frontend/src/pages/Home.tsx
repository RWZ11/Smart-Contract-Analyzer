import { Button } from "@/components/ui/button";
import { Shield, Zap, FileCode } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="space-y-8">
      <section className="text-center py-12 space-y-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          保障 Web3 世界的每一行代码
        </h1>
        <p className="text-gray-400 max-w-2xl mx-auto">
          基于静态分析与 AI 辅助的智能合约漏洞检测平台。
          支持 Solidity 全版本，覆盖 50+ 种常见漏洞模式。
        </p>
        <div className="flex justify-center gap-4 pt-4">
          <Button size="lg" onClick={() => navigate('/analyzer')}>开始审计</Button>
          <Button size="lg" variant="outline" onClick={() => window.open('https://github.com/crytic/slither', '_blank')}>
            了解更多
          </Button>
        </div>
      </section>

      <div className="grid md:grid-cols-3 gap-6">
        <Card 
          icon={<Zap className="text-yellow-400" />}
          title="极速分析"
          desc="毫秒级 AST 解析与漏洞扫描，无需等待漫长的编译过程。"
        />
        <Card 
          icon={<Shield className="text-green-400" />}
          title="全面覆盖"
          desc="检测重入攻击、整数溢出、未授权访问等多种高危漏洞。"
        />
        <Card 
          icon={<FileCode className="text-blue-400" />}
          title="精准定位"
          desc="精确定位到代码行，提供详细的修复建议与数据流追踪。"
        />
      </div>
    </div>
  );
}

function Card({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="bg-surface p-6 rounded-lg border border-gray-700 hover:border-primary transition-colors">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-400">{desc}</p>
    </div>
  );
}
