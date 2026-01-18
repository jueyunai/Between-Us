/**
 * Emoji 表情选择器
 * 轻量级实现，无需外部依赖
 */

// 常用表情分类
const EMOJI_CATEGORIES = {
    '常用': ['😊', '😂', '🥰', '😍', '🤗', '😘', '😭', '😢', '😅', '😆', '🤣', '😉', '😌', '😔', '😳', '🥺', '😤', '😡', '🤔', '😎'],
    '情感': ['❤️', '💕', '💖', '💗', '💓', '💞', '💝', '💘', '💟', '💌', '💋', '💏', '💑', '🫶', '🤝', '👫', '👬', '👭', '🫂', '💪'],
    '手势': ['👍', '👎', '👏', '🙏', '🤝', '✊', '👊', '🤛', '🤜', '🤞', '✌️', '🤟', '🤘', '👌', '🤌', '🤏', '👈', '👉', '👆', '👇'],
    '表情': ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '😚', '😙'],
    '其他': ['🎉', '🎊', '🎈', '🎁', '🎂', '🍰', '🌹', '🌸', '🌺', '🌻', '🌼', '🌷', '💐', '🌟', '⭐', '✨', '💫', '🔥', '💯', '👑']
};

class EmojiPicker {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            position: options.position || 'top', // 'top' 或 'bottom'
            categories: options.categories || EMOJI_CATEGORIES,
            onSelect: options.onSelect || null,
            ...options
        };
        
        this.picker = null;
        this.isOpen = false;
        this.init();
    }

    init() {
        // 创建触发按钮
        this.createTriggerButton();
        // 创建选择器面板
        this.createPicker();
        // 绑定事件
        this.bindEvents();
    }

    createTriggerButton() {
        // 查找输入框的父容器
        const wrapper = this.input.closest('.chat-input') || this.input.parentElement;
        
        // 创建按钮
        this.triggerBtn = document.createElement('button');
        this.triggerBtn.className = 'emoji-trigger-btn';
        this.triggerBtn.innerHTML = '😊';
        this.triggerBtn.type = 'button';
        this.triggerBtn.setAttribute('aria-label', '选择表情');
        
        // 插入到输入框前面
        wrapper.insertBefore(this.triggerBtn, this.input);
    }

    createPicker() {
        this.picker = document.createElement('div');
        this.picker.className = 'emoji-picker';
        this.picker.style.display = 'none';
        
        // 创建分类标签
        const tabs = document.createElement('div');
        tabs.className = 'emoji-tabs';
        
        Object.keys(this.options.categories).forEach((category, index) => {
            const tab = document.createElement('button');
            tab.className = 'emoji-tab' + (index === 0 ? ' active' : '');
            tab.textContent = category;
            tab.dataset.category = category;
            tab.type = 'button';
            tabs.appendChild(tab);
        });
        
        // 创建表情网格
        const grid = document.createElement('div');
        grid.className = 'emoji-grid';
        
        // 默认显示第一个分类
        const firstCategory = Object.keys(this.options.categories)[0];
        this.renderEmojis(grid, firstCategory);
        
        this.picker.appendChild(tabs);
        this.picker.appendChild(grid);
        
        // 添加到body
        document.body.appendChild(this.picker);
    }

    renderEmojis(grid, category) {
        grid.innerHTML = '';
        const emojis = this.options.categories[category];
        
        emojis.forEach(emoji => {
            const btn = document.createElement('button');
            btn.className = 'emoji-item';
            btn.textContent = emoji;
            btn.type = 'button';
            btn.dataset.emoji = emoji;
            grid.appendChild(btn);
        });
    }

    bindEvents() {
        // 点击触发按钮
        this.triggerBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });

        // 点击分类标签
        this.picker.querySelector('.emoji-tabs').addEventListener('click', (e) => {
            if (e.target.classList.contains('emoji-tab')) {
                // 更新激活状态
                this.picker.querySelectorAll('.emoji-tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                e.target.classList.add('active');
                
                // 渲染对应分类的表情
                const category = e.target.dataset.category;
                const grid = this.picker.querySelector('.emoji-grid');
                this.renderEmojis(grid, category);
            }
        });

        // 点击表情
        this.picker.querySelector('.emoji-grid').addEventListener('click', (e) => {
            if (e.target.classList.contains('emoji-item')) {
                const emoji = e.target.dataset.emoji;
                this.selectEmoji(emoji);
            }
        });

        // 点击外部关闭
        document.addEventListener('click', (e) => {
            if (this.isOpen && !this.picker.contains(e.target) && e.target !== this.triggerBtn) {
                this.close();
            }
        });
    }

    selectEmoji(emoji) {
        // 插入到输入框光标位置
        const start = this.input.selectionStart;
        const end = this.input.selectionEnd;
        const text = this.input.value;
        
        this.input.value = text.substring(0, start) + emoji + text.substring(end);
        
        // 恢复光标位置
        const newPos = start + emoji.length;
        this.input.setSelectionRange(newPos, newPos);
        this.input.focus();
        
        // 触发回调
        if (this.options.onSelect) {
            this.options.onSelect(emoji);
        }
        
        // 关闭选择器
        this.close();
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        // 计算位置
        const rect = this.triggerBtn.getBoundingClientRect();
        const pickerHeight = 320; // 选择器高度
        
        if (this.options.position === 'top') {
            // 显示在输入框上方
            this.picker.style.bottom = `${window.innerHeight - rect.top + 8}px`;
            this.picker.style.top = 'auto';
        } else {
            // 显示在输入框下方
            this.picker.style.top = `${rect.bottom + 8}px`;
            this.picker.style.bottom = 'auto';
        }
        
        this.picker.style.left = `${rect.left}px`;
        this.picker.style.display = 'block';
        this.isOpen = true;
        
        // 添加动画
        requestAnimationFrame(() => {
            this.picker.classList.add('show');
        });
    }

    close() {
        this.picker.classList.remove('show');
        setTimeout(() => {
            this.picker.style.display = 'none';
            this.isOpen = false;
        }, 200);
    }

    destroy() {
        if (this.picker) {
            this.picker.remove();
        }
        if (this.triggerBtn) {
            this.triggerBtn.remove();
        }
    }
}

// 导出
window.EmojiPicker = EmojiPicker;
