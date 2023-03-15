"use client"

import classNames from "classnames";
import React, { PropsWithChildren, useState } from "react";
import Navbar from "./Navbar";
// import SideBar from "./SideBar";

import TempSideBar from "./TempSideBar";

const SideBarLayout = (props: PropsWithChildren) => {
  const [collapsed, setSidebarCollapsed] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  return (
    <div
      className={classNames({
        "grid bg-[#202123] min-h-screen": true,
        "grid-cols-sidebar": !collapsed,
        "grid-cols-sidebar-collapsed": collapsed,
        "transition-[grid-template-columns] duration-300 ease-in-out": true,
      })}
    >
      <TempSideBar
      collapsed={collapsed}
      setCollapsed={() => setSidebarCollapsed((prev) => !prev)}
      shown={showSidebar}
      ></TempSideBar>
    </div>
  );
};

export default SideBarLayout;

// // components/Layout.tsx
// import classNames from "classnames";
// import React, { PropsWithChildren, useState } from "react";
// import { Bars3Icon } from "@heroicons/react/24/outline";
// import SideBar from "./SideBar";
// import Navbar from "./Navbar";

// const Layout = (props: PropsWithChildren) => {
//   const [collapsed, setSidebarCollapsed] = useState(false);
//   const [showSidebar, setShowSidebar] = useState(true);

//   return (
//     <div
//       className={classNames({
//         // 👇 use grid layout
//         "grid min-h-screen": true,
//         // 👇 toggle the width of the sidebar depending on the state
//         "grid-cols-sidebar": !collapsed,
//         "grid-cols-sidebar-collapsed": collapsed,
//         // 👇 transition animation classes
//         "transition-[grid-template-columns] duration-300 ease-in-out": true,
//       })}
//     >
//       {/* sidebar */}


//       <div>
//         <Navbar onMenuButtonClick={() => setShowSidebar((prev) => !prev)} />
//         {props.children}
//       </div>
//       {/* <SideBar></SideBar> */}
//     </div>
//   );
// };
// export default Layout;
