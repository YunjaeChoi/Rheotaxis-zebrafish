import * as React from 'react';
import { connect } from 'react-redux';
import {
  Button,
} from 'semantic-ui-react'
import 'semantic-ui-css/semantic.min.css'

interface Props {
  value: number;
}

interface State {

}

class Counter extends React.Component<Props, State> {

  render() {
    return (
      <div>
        <h1>카운터</h1>
        <h3>{this.state.value}</h3>
        <Button onClick={this.props.onIncrement}>+</Button>
        <Button onClick={this.props.onDecrement}>-</Button>
        <Button >start</Button>
        <Button >stop</Button>
      </div>
    );
  }
}


const INCREMENT = 'INCREMENT';
const DECREMENT = 'DECREMENT';

function increment(payload) {
  return {
      type: INCREMENT,
      payload
  };
};

function decrement(payload) {
  return {
      type: DECREMENT,
      payload
  };
};


const counter = (state = { value: 0 }, action) => {
    switch(action.type) {
        case INCREMENT:
            return Object.assign({}, state, {
                value: state.value + 1
            });
        case DECREMENT:
            return Object.assign({}, state, {
                value: state.value - 1
            });
        default:
            return state;
    }
};

const mapStateToProps = (state) => {
    return {
        value: state.counter.value
    };
}

const mapDispatchToProps = (dispatch) => {
    return {
        onIncrement: () => dispatch(increment()),
        onDecrement: () => dispatch(decrement())
    }
}

export default connect(mapStateToProps, mapDispatchToProps)(Counter);
