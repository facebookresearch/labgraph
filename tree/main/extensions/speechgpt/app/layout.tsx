
import SideBar from '../components/SideBar';
import '../styles/globals.css';

import SessionProvider from "../components/SessionProvider"
import {getServerSession} from "next-auth"

import {authOptions} from "../pages/api/auth/[...nextauth]"
import Login from '../components/Login';
import ClientProvider from '../components/ClientProvider';
import SideBarLayout from '../components/SideBarLayout';

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {

  const session = await getServerSession(authOptions)

  // printed in server
  // console.log(session);
  return (  
    <html>
      <head />
      <body>
        <SessionProvider session={session}>
          {
            !session ? (<Login></Login>) :
             (
              <div className="flex ">
              <div className="">
                <SideBarLayout />
              </div>
              
              <ClientProvider />
              
              <div className="bg-[#ffff] flex-1">{children}</div>
            </div>
            )

          }
  
        </SessionProvider>
      </body>
    </html>
  );
}
