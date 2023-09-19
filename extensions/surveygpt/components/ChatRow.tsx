import Link from 'next/link';
import React, { useEffect, useState } from 'react';
import { ChatBubbleLeftIcon, TrashIcon } from '@heroicons/react/24/outline';
import { usePathname, useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useCollection } from 'react-firebase-hooks/firestore';
import { collection, deleteDoc, doc, orderBy, query } from 'firebase/firestore';
import { db } from '../firebase';
import { groupCollapsed } from 'console';

type Props = {
  id: string;
  collapsed: boolean;
};

const ChatRow = ({ id, collapsed }: Props) => {
  const pathname = usePathname();
  const router = useRouter();
  const { data: session } = useSession();
  const [active, setActive] = useState(false);

  const [messages] = useCollection(
    collection(db, 'users', session?.user?.email!, 'chats', id, 'messages')
  );

  useEffect(() => {
    if (!pathname) return;

    setActive(pathname.includes(id));
  }, [pathname]);

  const removeChat = async () => {
    await deleteDoc(doc(db, 'users', session?.user?.email!, 'chats', id));
    router.replace('/');
  };

  return (
    <div>
      <Link
        className={`rounded-lg px-5 py-3 text-sm flex items-center justify-center space-x-2 hover:bg-custom-gray-200 cursor-pointer transition-all duration-200 ease-out ${
          active && 'bg-custom-gray-100'
        }`}
        href={`/chat/${id}`}
      >
        <ChatBubbleLeftIcon className="w-5 h-5"></ChatBubbleLeftIcon>
        <p className="flex-1 hidden truncate md:inline-flex text-gray-700/80">
          {messages?.docs[messages?.docs.length - 1]?.data().text || 'New Chat'}
        </p>
        {collapsed ? (
          ''
        ) : (
          <TrashIcon
            onClick={removeChat}
            className="w-5 h-5 text-gray-700 hover:text-red-700"
          ></TrashIcon>
        )}
      </Link>
    </div>
  );
};

export default ChatRow;
