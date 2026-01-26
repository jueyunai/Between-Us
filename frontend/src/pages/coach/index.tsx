import React, { useEffect, useState, useRef } from 'react'
import { View, Text, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { Input, Button } from '@nutui/nutui-react-taro'
import { sendCoachMessage, getCoachHistory, clearCoachHistory } from '../../services/api'
import './index.scss'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

const CoachPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollViewRef = useRef<any>(null)

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    const res = await getCoachHistory()
    if (res.success && res.data?.messages) {
      setMessages(res.data.messages)
      scrollToBottom()
    }
  }

  const scrollToBottom = () => {
    setTimeout(() => {
      Taro.pageScrollTo({ scrollTop: 99999, duration: 300 })
    }, 100)
  }

  const handleSend = async () => {
    const text = inputValue.trim()
    if (!text || loading) return

    // 添加用户消息
    const userMsg: Message = {
      id: Date.now(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInputValue('')
    scrollToBottom()

    // 发送请求
    setLoading(true)
    try {
      const res = await sendCoachMessage(text)
      if (res.success && res.data?.reply) {
        const aiMsg: Message = {
          id: Date.now() + 1,
          role: 'assistant',
          content: res.data.reply,
          created_at: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, aiMsg])
        scrollToBottom()
      } else {
        Taro.showToast({ title: res.message || '发送失败', icon: 'none' })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleClear = async () => {
    Taro.showModal({
      title: '提示',
      content: '确定要清空聊天记录吗？',
      success: async (result) => {
        if (result.confirm) {
          const res = await clearCoachHistory()
          if (res.success) {
            setMessages([])
            Taro.showToast({ title: '已清空', icon: 'success' })
          }
        }
      },
    })
  }

  return (
    <View className='coach-page'>
      <View className='chat-header'>
        <View className='header-left'>
          <Text className='header-icon'>🧘</Text>
          <View className='header-info'>
            <Text className='header-title'>AI 情感教练</Text>
            <Text className='header-status'>在线</Text>
          </View>
        </View>
        <Button className='clear-btn' size='small' fill='none' onClick={handleClear}>
          清空
        </Button>
      </View>

      <ScrollView className='chat-messages' scrollY scrollWithAnimation>
        {messages.length === 0 ? (
          <View className='empty-state'>
            <Text className='empty-icon'>💝</Text>
            <Text className='empty-text'>有什么想聊的吗？</Text>
            <Text className='empty-hint'>我是你的 AI 情感教练，随时倾听你的心声</Text>
          </View>
        ) : (
          messages.map((msg) => (
            <View
              key={msg.id}
              className={`message-item ${msg.role === 'user' ? 'user' : 'assistant'}`}
            >
              <View className='message-avatar'>
                {msg.role === 'user' ? '😊' : '🧘'}
              </View>
              <View className='message-bubble'>
                <Text className='message-text'>{msg.content}</Text>
              </View>
            </View>
          ))
        )}
        {loading && (
          <View className='message-item assistant'>
            <View className='message-avatar'>🧘</View>
            <View className='message-bubble typing'>
              <Text className='typing-dot'>●</Text>
              <Text className='typing-dot'>●</Text>
              <Text className='typing-dot'>●</Text>
            </View>
          </View>
        )}
      </ScrollView>

      <View className='chat-input-area'>
        <Input
          className='chat-input'
          placeholder='输入你想说的话...'
          value={inputValue}
          onChange={(val) => setInputValue(val)}
          onConfirm={handleSend}
        />
        <Button
          className='send-btn'
          type='primary'
          size='small'
          loading={loading}
          disabled={!inputValue.trim()}
          onClick={handleSend}
        >
          发送
        </Button>
      </View>
    </View>
  )
}

export default CoachPage
