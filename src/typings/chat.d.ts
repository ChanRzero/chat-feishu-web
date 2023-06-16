declare namespace Chat {


	interface ChatMessage {
		role: string;
		id: string;
		parentMessageId: string;
		text: string;
		delta: string;
	  }

	interface Chat {
		msgCache: string[]
		dateTime: string
		text: string
		inversion?: boolean
		error?: boolean
		loading?: boolean
		role: string
		conversationOptions?: ConversationRequest | null
		requestOptions: { prompt: string; options?: ConversationRequest | null;role: string }
	}

	interface History {
		title: string
		isEdit: boolean
		uuid: number
	}

	interface ChatState {
		active: number | null
		usingContext: boolean;
		history: History[]
		chat: { uuid: number; data: Chat[] }[]
	}

	interface ConversationRequest {
		conversationId?: string
		parentMessageId?: string
		contextMessage?: {role: string,content: string}[]
	}

	interface errorRespose {
		status: boolean
		data: any
		message: string
	}


	interface ConversationResponse {
		conversationId: string
		detail: {
			choices: { finish_reason: string; index: number; logprobs: any; text: string }[]
			created: number
			id: string
			model: string
			object: string
			usage: { completion_tokens: number; prompt_tokens: number; total_tokens: number }
		}
		id: string
		parentMessageId: string
		role: string
		text: string
	}
}
