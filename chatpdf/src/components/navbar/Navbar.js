import './navbar.scss'
import {
    SettingsOutlined,
    HomeOutlined,
    Home,
    MoveToInboxOutlined,
    SmartToy,
    PeopleAlt,
    PermContactCalendar,
    ShowChart,
    ModelTraining,
    HelpOutline,
    DataSaverOff,
    Person

  } from "@mui/icons-material";
  
const Navbar = ({title}) => {
    const pageTitle = title
    return (
        <div className='navbar'>
            {
                pageTitle === "Settings" && 
                    <div className='left_nav'>
                        <SettingsOutlined className='icon'/>
                        <h3 className='navTitle' style={{paddingLeft: "10px"}}>{pageTitle}</h3>
                    </div>
                
            }
            {
                pageTitle === "Training" && 
                    <div className='left_nav'>
                        <ModelTraining className='icon'/>
                        <h3 className='navTitle' style={{paddingLeft: "10px"}}>{pageTitle}</h3>
                    </div>
            }
            {
                pageTitle === "Dashboard" && 
                    <div className='left_nav'>
                        <Home className='icon'/>
                        <h3 className='navTitle' style={{paddingLeft: "10px"}}>{pageTitle}</h3>
                    </div>
            }

            <div className='right_nav'>
                <HelpOutline className='icon'/>
                <DataSaverOff className='icon'/>
                <button className='upgrade'>Upgrade</button>
                <Person className='icon_avatar'/>

            </div>
        </div>
    )

}
export default Navbar