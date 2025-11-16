#!/usr/bin/env python3
import argparse
import os
import sys
from rag.rag_system import RAG

def main():
    parser = argparse.ArgumentParser(description="RAG系统命令行工具")
    parser.add_argument(
        "--file", 
        "-f", 
        help="要处理的单个文件路径"
    )
    parser.add_argument(
        "--directory", 
        "-d", 
        help="要处理的目录路径"
    )
    parser.add_argument(
        "--extensions", 
        "-e", 
        nargs="+", 
        default=[".pdf", ".txt", ".csv", ".docx"],
        help="要处理的文件扩展名列表 (默认: .pdf .txt .csv .docx)"
    )
    parser.add_argument(
        "--collection", 
        "-c", 
        default="documents",
        help="Milvus集合名称 (默认: documents)"
    )
    
    args = parser.parse_args()
    
    # 检查参数
    if not args.file and not args.directory:
        print("错误: 必须指定 --file 或 --directory 参数")
        parser.print_help()
        sys.exit(1)
    
    if args.file and args.directory:
        print("错误: 不能同时指定 --file 和 --directory 参数")
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.file:
            # 处理单个文件
            if not os.path.exists(args.file):
                print(f"错误: 文件 '{args.file}' 不存在")
                sys.exit(1)
                
            print(f"正在处理文件: {args.file}")
            RAG.add_file(args.file, args.collection)
            print(f"文件 '{args.file}' 已成功添加到集合 '{args.collection}'")
            
        elif args.directory:
            # 处理目录
            if not os.path.exists(args.directory):
                print(f"错误: 目录 '{args.directory}' 不存在")
                sys.exit(1)
                
            if not os.path.isdir(args.directory):
                print(f"错误: '{args.directory}' 不是一个目录")
                sys.exit(1)
                
            print(f"正在处理目录: {args.directory}")
            print(f"文件扩展名: {', '.join(args.extensions)}")
            RAG.process_directory(args.directory, args.extensions, args.collection)
            print(f"目录 '{args.directory}' 已成功处理，数据存储在集合 '{args.collection}'")
            
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()