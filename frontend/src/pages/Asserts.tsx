import React, { useState, useEffect } from 'react';
import { Card, Tree, Spin, message, Empty, Breadcrumb, Typography, Button, Space } from 'antd';
import { FileTextOutlined, FolderOutlined, FolderOpenOutlined, RightOutlined, DownloadOutlined } from '@ant-design/icons';
import { assertsApi, FileItem, FileContent } from '../services/api';
import MarkdownRenderer from '../components/MarkdownRenderer';

const { Title, Text } = Typography;

interface TreeNode {
  title: string;
  key: string;
  isLeaf: boolean;
  icon: React.ReactNode;
  children?: TreeNode[];
}

const Asserts: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [structure, setStructure] = useState<{ summary_dates: string[]; output_files: string[] } | null>(null);
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileContent | null>(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState<string[]>(['资源文件']);

  // 加载目录结构
  useEffect(() => {
    loadStructure();
  }, []);

  const loadStructure = async () => {
    setLoading(true);
    try {
      const data = await assertsApi.getStructure();
      setStructure(data);
      
      // 构建树形数据
      const nodes: TreeNode[] = [];
      
      // 添加summary节点（按日期）
      if (data.summary_dates && data.summary_dates.length > 0) {
        const summaryNode: TreeNode = {
          title: '摘要汇总 (summary)',
          key: 'summary',
          isLeaf: false,
          icon: <FolderOpenOutlined />,
          children: data.summary_dates.map(date => ({
            title: date,
            key: `summary/${date}`,
            isLeaf: false,
            icon: <FolderOutlined />,
            children: [] // 动态加载
          }))
        };
        nodes.push(summaryNode);
      }
      
      // 添加output节点
      if (data.output_files && data.output_files.length > 0) {
        const outputNode: TreeNode = {
          title: '分析汇总 (output)',
          key: 'output',
          isLeaf: false,
          icon: <FolderOpenOutlined />,
          children: data.output_files.map(file => ({
            title: file,
            key: `output/${file}`,
            isLeaf: true,
            icon: <FileTextOutlined />
          }))
        };
        nodes.push(outputNode);
      }
      
      setTreeData(nodes);
    } catch (error) {
      message.error('加载目录结构失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // 动态加载子节点
  const loadChildren = async (folder: string): Promise<TreeNode[]> => {
    try {
      const files = await assertsApi.getFiles(folder);
      return files.map(file => ({
        title: file.name,
        key: file.path,
        isLeaf: !file.is_dir,
        icon: file.is_dir ? <FolderOutlined /> : <FileTextOutlined />
      }));
    } catch (error) {
      console.error('加载子节点失败:', error);
      return [];
    }
  };

  // 树节点加载数据
  const onLoadData = async (node: TreeNode) => {
    if (node.isLeaf) return;
    
    const children = await loadChildren(node.key);
    setTreeData(prev => updateTreeData(prev, node.key, children));
  };

  const updateTreeData = (nodes: TreeNode[], key: string, children: TreeNode[]): TreeNode[] => {
    return nodes.map(node => {
      if (node.key === key) {
        return { ...node, children };
      }
      if (node.children) {
        return { ...node, children: updateTreeData(node.children, key, children) };
      }
      return node;
    });
  };

  // 选择文件
  const onSelect = async (selectedKeys: React.Key[]) => {
    if (selectedKeys.length === 0) return;
    
    const key = selectedKeys[0] as string;
    // 找到对应的节点
    const findNode = (nodes: TreeNode[]): TreeNode | undefined => {
      for (const node of nodes) {
        if (node.key === key) return node;
        if (node.children) {
          const found = findNode(node.children);
          if (found) return found;
        }
      }
      return undefined;
    };
    
    const node = findNode(treeData);
    if (node?.isLeaf) {
      // 更新面包屑
      const pathParts = key.split('/');
      setBreadcrumbs(['资源文件', ...pathParts.slice(0, -1)]);
      
      // 加载文件内容
      await loadFileContent(key);
    }
  };

  // 加载文件内容
  const loadFileContent = async (path: string) => {
    setFileLoading(true);
    try {
      const content = await assertsApi.getContent(path);
      setSelectedFile(content);
    } catch (error) {
      message.error('加载文件内容失败');
      console.error(error);
    } finally {
      setFileLoading(false);
    }
  };

  // 返回上一级
  const goBack = () => {
    setSelectedFile(null);
    setBreadcrumbs(['资源文件']);
  };

  // 下载文件
  const handleDownload = () => {
    if (selectedFile) {
      assertsApi.download(selectedFile.path);
    }
  };

  return (
    <div className="p-6">
      <Title level={3}>📁 资源文件浏览</Title>
      <Text type="secondary" className="mb-4 block">
        浏览淘股吧博主帖子摘要与分析汇总
      </Text>
      
      <div className="flex gap-4">
        {/* 左侧目录树 */}
        <Card 
          title="目录结构" 
          style={{ width: 350 }}
          className="flex-shrink-0"
        >
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <Spin size="large" />
            </div>
          ) : treeData.length === 0 ? (
            <Empty description="暂无数据" />
          ) : (
            <Tree
              showIcon
              defaultExpandAll
              treeData={treeData}
              onSelect={onSelect}
              loadData={onLoadData}
            />
          )}
        </Card>
        
        {/* 右侧文件内容 */}
        <Card 
          className="flex-1"
          bodyStyle={{ height: 'calc(100vh - 240px)', overflow: 'auto' }}
        >
          {fileLoading ? (
            <div className="flex justify-center items-center h-full">
              <Spin size="large" />
            </div>
          ) : selectedFile ? (
            <>
              <div className="flex items-center justify-between mb-4">
                <Breadcrumb
                  items={breadcrumbs.map((item, index) => ({
                    key: index,
                    title: index === breadcrumbs.length - 1 ? (
                      <span>{selectedFile.name}</span>
                    ) : (
                      item
                    )
                  }))}
                  separator={<RightOutlined />}
                />
                <Space>
                  <Button 
                    icon={<DownloadOutlined />} 
                    onClick={handleDownload}
                  >
                    下载
                  </Button>
                  <Button onClick={goBack}>
                    返回列表
                  </Button>
                </Space>
              </div>
              <MarkdownRenderer content={selectedFile.content} />
            </>
          ) : (
            <Empty 
              description="请选择左侧文件查看内容" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              className="flex flex-col items-center justify-center h-full"
            />
          )}
        </Card>
      </div>
    </div>
  );
};

export default Asserts;
